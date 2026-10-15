# Group profiles

`get_group_profile` makes a short-lived, read-only observation under an explicitly
expected Telegram account. It returns a description and available counts, with
optional pinned messages. Authenticate separately first.

```python
from tgdata import TgData, GroupProfile

async def inspect(config_path, expected_account_id):
    async with TgData(config_path, interactive_login=False) as tg:
        profile = await tg.get_group_profile(
            "@example_group",
            account_id=expected_account_id,
            pinned_limit=5,
            heartbeat=lambda phase: print(phase),
        )
        print(profile.about, profile.group.participants_count, profile.online_count)
        print(profile.pins_status, profile.pins_total, profile.pins_total_exact)
        for pin in profile.pinned_messages:
            print(pin.id, pin.date, pin.kind, pin.text)
        return profile.to_dict()
```

## Inputs and requests

`account_id` is required and must be a positive Python integer, excluding bool.
The actual authenticated account must match before group work; a stale cached
identity is not authority. Reference parsing and numeric cache requirements are
the same as [lookup_group](group_operations.md).

Supported full profiles are basic groups, supergroups and broadcast channels.
An already-member or peek invite can supply a usable group peer. A plain invite
preview, a minimal/hashless channel without a usable peer, a Community or an
unknown channel type raises GroupReferenceError instead of inventing a profile.
Use lookup_group to inspect an invite preview without a full peer.

`pinned_limit=0` is the default and disables the pin search. An explicit integer
from 1 through 100 requests **one** filtered search response, with at most that
many message slots. There is no pagination, lookahead, topic traversal, media
download or automatic join. A larger collection is outside this operation's
contract. Limits outside 0..100, booleans and non-integers raise ValueError
before opening a client.

After resolution, metadata uses one logical GetFullChat/GetFullChannel request;
pins add one logical Search request with the pinned filter and hash=0.
Authentication, resolution and budget identity proof are separate source calls.
The operation does not use or change the persistent client/pool or current_group.

## Returned values

GroupProfile and GroupPinnedMessage are frozen dataclasses. Returned pin records
form an immutable tuple. Each to_dict() creates detached plain dictionaries/lists
with integer IDs and UTC ISO8601 timestamps, suitable for JSON. Neither value
contains SDK entities, access hashes, clients or member lists.

| GroupProfile field | Meaning |
|---|---|
| account_id, target | Verified owner and normalized input; invite tokens are replaced by the existing hashed label |
| group | GroupMetadata from the matching full response: canonical peer ID, name, type and optional participant count |
| about | Complete description; an observed empty description is an empty string |
| online_count | ChannelFull's observed online count when supplied; None for absent values and basic groups |
| observed_at | Local UTC receipt/projection time for full metadata |
| pinned_messages | Tuple of GroupPinnedMessage values, in source order |
| pins_status | Coverage state described below |
| pins_total | Source search total, or None when no successful pin response exists |
| pins_total_exact | True for an exact count, False for an inexact count, None without a successful response |
| pins_observed_at | Separate local UTC receipt/projection time for pins, or None |

For channels, participant count comes from ChannelFull; an absent value does not
fall back to an older count from resolution. For basic groups it comes from the
matching Chat metadata, not the length of a user/participant vector. None means
unavailable, while 0 is an observed zero. Counts do not form an atomic census:
online_count is not forced to be smaller than participant count.

GroupPinnedMessage contains id, kind, date and text. A normal message has
kind='message', its original date and complete text, including an empty media
caption. A service message has kind='service', its original date and text=None.
An unavailable MessageEmpty placeholder has kind='unavailable', its ID and
date/text=None. Dates are normalized to UTC. No sender/contact enrichment is
performed. These are results of the pinned filter, not observations of pin time
or a promise that each message remains pinned later.

## Pin coverage

| Status | Meaning |
|---|---|
| not_requested | Default; no pin read was attempted, total/precision/time are unknown |
| complete | Exact source total equals all returned readable/service records; includes a valid empty response with total=0 |
| limited | Exact total exceeds the requested full response; caller limit was reached and all returned records are available |
| incomplete | Source marks results inexact, some rows are unavailable, or a short slice reports more results |
| failed | Only on an exception's partial_result: metadata completed but optional pin reading/projection failed |

Count precision is independent of content completeness. An exact total of ten
with an unavailable message remains pins_total_exact=True and pins_status='incomplete'.
An approximate total of ten has pins_total_exact=False. Short responses alone
are not proof of completion. Malformed/wrong-peer/duplicate/oversized responses
raise instead of being converted into complete or empty observations.

Metadata and pins may change between their separate requests. Completion means
the validated response describes a complete result for that observation; it does
not promise every historical/private pin is visible or an atomic global snapshot.
A profile or pin result does not establish membership or general history access.
Use check_group_access for the existing explicit history probe.

## Errors, budget and liveness

Full metadata failure raises the original source/cache error, or GroupResponseError
for invalid projected data. No full profile is fabricated. Optional pin failure
also raises the original error, preserving its type/object. When it supports
attributes, error.partial_result holds the completed GroupProfile with
pins_status='failed' and no accepted pin response. A denied read, wait, budget
refusal or transport error therefore cannot be mistaken for an empty pin list.
Exception annotation is best effort; a custom exception that refuses attributes
still propagates unchanged. No rows from a malformed pin response are accepted.

```python
try:
    profile = await tg.get_group_profile(
        "@example_group", account_id=expected_account_id, pinned_limit=5)
except Exception as error:
    partial = getattr(error, "partial_result", None)
    if isinstance(partial, GroupProfile):
        save_profile_observation(partial.to_dict())  # caller-defined storage
    raise
```

Metadata costs no message allowance. With ReadBudget configured, the pin request
re-verifies the same owner and reserves pinned_limit slots before sending; unused
slots are refunded from a successful response. Exhausted allowance raises before
send, even if fewer pins might exist. Choose a smaller limit explicitly if needed.
Failed/cancelled attempts keep their existing conservative charge. No new policy
is created, and no allowance is reset.

The optional synchronous heartbeat uses the existing [liveness contract](batch_heartbeat.md):
actual SDK request/answer/error phases plus 'profile done' and 'pins done'.
It does not tick while a request is unanswered. Callback errors are logged by
type and ignored; invalid async/non-callable callbacks raise the existing
BatchFormatError (a ValueError) before connection.

The verified temporary client's zero automatic wait/retry policy is unchanged.
Telegram waits propagate; SDK's final server-error backoff can still occur.
There is no new retry loop or shared-client setting mutation.

## Health and cleanup

Actual source RPC failures populate get_account_health(account_id), including a
pin denial even though metadata completed. Local conversion, storage and callback
errors do not manufacture Telegram verdicts. Neither metadata nor filtered-pin
success clears a prior group-denial record; request/account recovery otherwise
follows the existing owned-health rules. Legacy health remains separate.

The existing [owned-operation cleanup contract](account_operations.md) applies:
settle one disconnect attempt; cleanup failure preserves the original result/error;
caller cancellation remains cancellation, including repeated cancellation during
teardown. A caller cancelling after the helper completed does not receive a promised
successful result. There is no shutdown timeout or atomic profile snapshot guarantee.

## Qualification

Run `python -m tgdata.smoke_tests.test_45_group_profile` on Telethon 1.45.0.
The suite exercises actual SDK dispatch, TL encoding/decoding, session backends,
SQLite budget admission and owned cleanup with synthetic source replies and
blocked sockets. This qualifies local composition, not live Telegram permissions
or the availability of optional fields for a particular account/group.
