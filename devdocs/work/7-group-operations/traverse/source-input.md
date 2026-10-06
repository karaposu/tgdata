# Source input — #7

## User request

$task-impl o [**\#7 — group lookup, access checks and joining**](<https://github.com/karaposu/tgdata/issues/7>).

## Referenced issue

Filed 2026-10-03 from a draft proposal written for a downstream consumer of tgdata (the proposal itself is not public). The request below keeps its own wording, trimmed to what tgdata itself would do.

**Request.** Three group operations, all as short-lived lookups (`ephemeral_client`):
- **look up a group:** its name, handle and type;
- **check access** for an account;
- **join** a group by invite link or handle, with a limit on how many joins an account makes.

These are Telegram questions, so they belong beside the reading.

**Today.**
- The pieces exist separately — `GroupInfo.from_entity`, `GroupAccessError`, `ephemeral_client` — but not as these operations, so callers write their own "can this account read it" and "what's this group's name and handle".
- **Nothing can join a group**, which private groups need before reading. Group discovery deliberately never joins.

**When it works.** Adding `@some_group` fills in its real name and type, checks that the assigned account can read it, and says "ready". For a private group it says "account 5 needs to join first", and joining is one call.
