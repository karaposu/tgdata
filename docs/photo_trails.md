# Optional photo-trail views

A person may send a text post or Telegram album and then add photos in separate
messages. `fold_photo_trails` can associate those original posts in a **provisional
current view**. This is a guess about intent, so it is disabled by default.

The helper performs no Telegram requests, storage, scheduling or acknowledgment.
Every original `TelegramPost`, caption, member ID and media reference survives.
Telegram album membership and this optional inference remain separate concepts.

## Enable the policy explicitly

```python
from tgdata import PhotoTrailPolicy, fold_photo_trails

# current_posts is the complete current observation set for your chosen scope.
# It contains original TelegramPost values, not an earlier inferred view.
view = fold_photo_trails(
    current_posts,
    policy=PhotoTrailPolicy(enabled=True),
)

originals = {post.post_id: post for post in view.posts}
for original_ids in view.groups:
    grouped_originals = [originals[key] for key in original_ids]
    # Each item still has all of its original members and captions.
    print(original_ids)

print(view.folded_posts, view.folded_photos)
```

Calling without a policy, or with `PhotoTrailPolicy()`, returns one group per
original post and zero fold counts. No existing tgdata call enables this feature.

`posts` must be a concrete list or tuple of `TelegramPost` values. A generator is
refused rather than consumed as an implicit stream. Identical duplicate
observations deduplicate when admitted under the work bounds. Different current
observations of the same post ID, or one raw message assigned to different posts,
raise `PhotoTrailError`. The helper does not choose an edit policy.

## What the rule can attach

The policy has these fields:

| Field | Default | Meaning |
|---|---|---|
| `enabled` | `False` | Explicit opt-in |
| `gap_seconds` | `30` | Maximum nonnegative gap from the preceding member |
| `max_span_seconds` | `120` | Maximum elapsed time from the anchor's last original member to the last attached photo |
| `max_photos` | `20` | Maximum attached original photo messages, excluding the anchor's own media |

`enabled` is a plain bool. The other fields are plain integers from 1 through
2,147,483,647; booleans, strings, floats, zero and negative values refuse. The
policy is immutable; `to_dict()` returns a copy and `from_dict()` validates the
four exact fields. Defaults are conservative choices, not measured guarantees
about human intent or Telegram album size.

An anchor is a text-bearing ordinary post or an actual Telegram album. All its
members must identify the same positive Telegram user and have known,
nondecreasing dates. The sender comes from each original message, not from the
account used to scrape it. Unknown, mixed or channel-style sender identities
cannot establish the same person.

A follower must contain only ordinary, textless photo messages. A singleton or a
photo-only Telegram album can attach; an entire original post attaches or stays
separate. Videos, documents and other media do not count as photo followers.
Whitespace-only text is treated as empty. Every caption remains in its original
member; the helper does not select a primary caption.

Every member's reply must be absent or point to an already known earlier member
of the anchor, attached chain or the same candidate post. Unknown, foreign, self
and future reply targets refuse that attachment. No reply-author lookup occurs.

Each member's gap must fit `gap_seconds`, including exact microsecond boundaries.
The whole candidate must fit the remaining photo count and total span. A failed
candidate remains separate and ends the old chain. A separate eligible text post
or album may start its own chain. A lone uncaptioned singleton photo does not
become an anchor for a later text. Text-to-text and photos-before-text inference
are not performed.

## Interleaving and later observations

The algorithm examines original message IDs, not merely the first position of
each album. An unknown author's album at IDs 1 and 5 must still interrupt a
known user's text at 2 and photos at 3 and 6 when its member at 5 is encountered.
Photo 3 may attach; photo 6 must not jump over that unknown activity.

Other positively identified users can interleave without interrupting each
other. Overlapping original-post ID intervals for the same user are treated as
ambiguous barriers. Missing dates and backward chronology also prevent a post
from anchoring or following. Chronology retains each individually known sender's
timestamps even when the enclosing album has mixed authors and cannot anchor.
Unknown or unsafe activity interrupts trails at each of its original member
positions. Whole-post decisions occur at the last currently observed member.

Input-list order does not affect a view of the same original observations. An
album can later acquire a caption, a different sender or a larger extent. A new
view may then withdraw a previous association. Its original posts remain
available; no prior `PhotoTrailView` or `TelegramPost` object is mutated.

**Replace the earlier view for the same application-selected scope.** Do not
append successive views as permanent final posts. Compare `revision` to avoid
processing an identical view again. Fold counts describe the current view, not
new work on each call; do not add them repeatedly on replay.

The helper sees only the observations supplied. It cannot discover omitted
messages or prove that Telegram has no unseen, deleted or inaccessible messages.
A batch end, quiet period, fixed window, budget refusal or restart is never a
global completeness signal. Every view has `status="provisional"`.

## Retain originals across batches and restarts

The application owns permanent records and the intended observation scope. The
repository's [album receiver](../examples/album_assembly.py) already stores
immutable original member records and collection-scoped recognition of accepted
raw inputs. The new [photo-trail example](../examples/photo_trails.py) adds a
read-only bounded view operation without changing that receiver's schema or
acceptance methods.

```python
from examples.album_assembly import AlbumReceiver
from examples.photo_trails import load_photo_trails
from tgdata import PhotoTrailPolicy

# Provision the intended collection once with create=True. Reopen thereafter:
receiver = AlbumReceiver("originals.sqlite3", "daily")

batch = await tg.sync_group(chat_id, limit=200)
if batch is not None:
    receiver.accept(batch)  # original records committed or exact acceptance confirmed
    await tg.acknowledge_sync(chat_id, batch.batch_id)

    view = load_photo_trails(
        receiver, chat_id,
        after_id=scope_start_id,       # retain this scope across relevant batches
        through_id=batch.next_after_id,
        policy=PhotoTrailPolicy(enabled=True),
    )
    application.replace_current_view(scope_key, view)  # your application operation
```

`scope_start_id`, `scope_key` and `application.replace_current_view` are caller
choices, not tgdata APIs. Do not move the lower boundary past a still-relevant
anchor just because source acknowledgment advanced. Recompute from the intended
retained originals after restart. A failure to load known storage must raise;
never replace it with a new empty collection or discard the previous application
view on failure.

For backfill, accept `turn.batch` and acknowledge its **full original**
`turn.delivery` using `await tg.acknowledge_backfill(turn.delivery)`. A photo-trail
revision, group ID or largest inferred member ID is not a source receipt.
Available partial data alone also does not establish a pending source delivery;
use the source's normal pending/recovery APIs before acknowledgment.

The example's explicit interval is `(after_id, through_id]` in one canonical
negative integer chat. Bounds are plain integers with
`0 <= after_id <= through_id <= 2,147,483,647`. It reads all currently stored
records inside the interval and requires every known member of each selected
post to fit inside it. If an album crosses either boundary, the view refuses:
choose a wider explicit interval. It does not silently expand or clip an album
and thereby hide a known intervening text. An empty valid interval produces an
empty view.

Schema/collection checks, key/count/byte preflight, post extents and payload reads
share one SQLite snapshot. Loading uses byte-exact collection/post comparisons.
The read transaction closes before pure inference. View generation performs no
writes, migrations or repairs. Known file/schema/collection loss and selected
data corruption raise; arbitrary external deletion or rollback of history still
requires the application's backup/archive recovery.

Original acceptance is separate from current-view work. A view can refuse its
scope or size while the already accepted raw input remains confirmable under its
unchanged input policy. Keep accepted data and its original source obligations;
do not require a growing inference view to confirm an old receipt.

## Resource limits and saved values

`fold_photo_trails`, `PhotoTrailView` and `PhotoTrailView.from_json` accept positive
plain-integer `max_members` and `max_bytes`. Defaults are 10,000 and 16 MiB.

For folding, `max_members` bounds inspected input member occurrences—including
duplicate supplied post observations—and retained unique output members.
`max_bytes` bounds the sum of all supplied post JSON bytes and resulting view
JSON bytes, using canonical UTF-8. A constructor/loader's byte bound applies to
the single encoded view. These are serialized-work bounds, not a strict RSS
guarantee. Limits refuse the whole operation; no original or relation is trimmed.

Raised bounds propagate through nested post validation and immutable getters,
including observations accumulated beyond one raw batch's 10,000-message cap.
Loading under stricter bounds can refuse a valid saved value; retain an adequate
policy rather than resetting the original data. The example uses its receiver's
configured member/byte bounds for selection, original loads and folding.

`PhotoTrailError` is a local format/conflict/policy/scope/work refusal, with no
content logging or Telegram health event. The example also propagates existing
receiver/post/storage errors. Cleanup failures do not replace primary read
failures. No live source or account state is changed by a view operation.

Original media modes stay with their original posts. A pure view can preserve
reference and download observations; it neither copies downloaded files nor
refreshes expired references. Keep media bytes durably as required by the raw
delivery contract. The receiver example remains reference-only.

## View format and properties

The format contains exactly these fields:

| Field | Meaning |
|---|---|
| `schema` | `"tgdata.photo-trail-view"` |
| `version` | Integer `1` |
| `algorithm` | `"same-user-photo-trail/v1"` |
| `status` | `"provisional"` |
| `policy` | The four validated policy fields |
| `posts` | Unique canonical ordered original TelegramPost v1 documents |
| `groups` | Objects with `anchor_post_id` and ordered `post_ids`, beginning with the anchor |
| `folded_posts` | Number of original nonanchor posts attached |
| `folded_photos` | Number of their original photo messages |
| `revision` | SHA-256 of canonical content excluding this field |

Originals and groups are ordered by numeric chat ID, first original member ID
and post ID. Every original post occurs in exactly one group. JSON uses sorted
keys, compact separators, UTF-8 text and no nonfinite values. Loaders reject
unknown/missing fields, duplicate JSON keys, invalid nested originals, conflicting
identities, bad order/types/counts/hash and unsupported schemas/algorithms. They
recompute the relation: rehashing a forged association does not make it valid.

`view.posts` is a tuple of immutable original posts. `view.groups` is a tuple of
post-ID tuples. `view.policy` is frozen; `revision`, `status`, `folded_posts` and
`folded_photos` expose the corresponding values. `to_dict()` returns a copy;
`to_json()` returns canonical text; `PhotoTrailView.from_json(text_or_bytes, ...)`
reloads it without network or storage.

## Offline demonstration and verification

```bash
python examples/photo_trails.py --demo
python -m tgdata.smoke_tests.test_43_photo_trails
```

The demo uses actual SQLite/source-engine components with synthetic messages and
blocked sockets. Tests also use Telethon 1.45.0 serialization, actual receiver and
daily/backfill engines, process exits and storage faults. This qualifies local
mechanics, not generic human-intent accuracy or hardware power-loss durability.
ScrapeOps adoption remains a separate change after review and merge.
