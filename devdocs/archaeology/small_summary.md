---
model: gpt-6-astra
effort: max
---

# What tgdata does

Source state: feature branch at35aead1, refreshed2026-10-06 from the library's
code and retained whole-source context. This describes implemented behavior,
including the known rejected-review cases, rather than a claim of live acceptance.

Tgdata is a Python library for programs that collect and monitor Telegram group
and channel messages using a logged-in user account. It is a building block for
scripts and data pipelines; it does not supply a website, job queue or worker
service of its own.

A caller can list accessible groups, fetch or search messages, count messages,
and receive new messages through polling or event callbacks. The established
interface returns tables that callers can filter, analyze and export. Message
media and profile photos can be downloaded when requested.

There is also a separate batch interface for storage and delivery. It returns
versioned, repeatable message records with a cursor and a content identifier.
Optional downloads are stored under names derived from their bytes, and completed
records remain available when later work fails. A caller still owns its durable
cursor and delivery acknowledgments.

Group discovery follows Telegram's recommendations, linked discussions and links
found in posts. Discovery itself does not join groups. The current feature branch
adds explicit lookup, read-access checking and joining as short-lived operations.
They distinguish group details, membership, a successful read, approval requested,
and required external interaction. Paid entry and webviews are described rather
than completed automatically.

Every client is built through shared account controls: configured proxy routing,
optional fixed device details, login checks and session persistence. Interactive
login is available through the explicit login policy; the short-lived group
operations do not prompt. Sessions normally use Telethon files, or a caller can
supply a store that keeps an opaque session string elsewhere.

Optional durable limits count explicit message reads. Joining requires a separate
configured account allowance on this branch. These limits are shared through
SQLite files, count admitted requests before sending, and retain uncertain charges.
They do not promise that a chosen rate prevents Telegram restrictions.

Health events report Telegram's waits, logouts, bans, restrictions and group-access
failures. Callbacks and a health summary expose those observations to the caller.
Two issues in the new group integration are reproduced and awaiting revision3:
exhausted temporary server failures can look like bad references, and the health
summary can attach a fresh event's observation to a stale cached account ID.
The feature is implemented but its PR remains rejected/draft until those defects
are addressed through the contribution workflow.

The package includes deterministic offline suites for account controls, session
storage, budgets, batches and group operations, alongside older account-dependent
smoke scripts. The current offline evidence does not replace live acceptance with
a designated account and group. Analysts, archive builders and application
developers can use the library's extraction pieces while owning their storage,
scheduling and product decisions.
