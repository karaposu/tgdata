# tgdata — what it is, from the code (refreshed at `784d851`, 2026-11-26, version 0.1.4)

## What it is

tgdata is a Python library that reads Telegram groups and channels through ordinary Telegram user accounts, not bots. A program logs an account in once, then asks tgdata for a group's messages, media and details. It gets them back as tables or as strict, versioned data files.

It sits on top of Telethon, a well-known Python Telegram client, and pins Telethon 1.45.0 for its multi-account features. It is a library first. It also ships two small command-line tools: one to log an account in by hand, and a background worker that takes reading jobs.

## What it does today

- **Reads messages.** It reads a group's history by date, by message number or in batches, with progress reports and "still alive" signals for long reads. It can also download each message's photos and files, or only the ones you pick later.
- **Produces versioned, replayable batches.** A read can come back as a fixed-format batch (version 1) with a stable ID and a "continue after this message" cursor, so a separate system can store it and pick up exactly where it left off.
- **Tracks daily and historical progress.** Optional stores remember how far each group has been delivered. A "daily continuation" reads what's new since last time. A "backfill" walks a group's older history in steps. Progress moves forward only when the receiver confirms it saved the data.
- **Finds new groups.** It uses Telegram's name search, "similar channels" recommendations, and t.me links mined from posts, paced carefully and budgeted, because looking up names is what Telegram punishes hardest.
- **Inspects groups without reading them.** It can look a group up, check whether an account can read it (by trying one message), get a group's profile and pinned messages, and measure activity over a time window. It can also join a group, but only within a configured join allowance.
- **Protects accounts:**
  - a per-account daily message allowance, with a slow warm-up for new accounts, checked before any request is sent;
  - a join allowance;
  - an optional proxy for every connection, with no silent fallback to a direct connection;
  - a fixed "device identity", so an account always looks like the same phone or computer;
  - never asking for a login code on its own in a background job.
- **Reports account health.** Every time Telegram says "wait", "you are logged out", "banned", "restricted" or "no access to this group", tgdata turns it into a plain event, and reports "ok" only when Telegram's answers prove the problem ended.
- **Keeps logins out of files, if wanted.** An application can keep each account's login in its own storage, such as a database, instead of `.session` files.
- **Logs in by hand, step by step.** A login flow (phone, then code, then optional password) can be driven from a terminal tool, or from an application that saves its progress between steps.
- **Runs several accounts.** An "account pool" reads a group through the first eligible account, skipping ones that are waiting, out of allowance, logged out or locked out of that group. It records why. A separate worker process takes JSON jobs (read, look up, check access, join) for a fixed list of accounts.
- **Assembles media views.** Optional helpers group multi-photo posts into albums, and build "photo trails" over repeated observations.

## What looks in progress or rough

- **Two generations side by side.** The original interface, which returns table-shaped results, sits alongside a newer, much stricter layer: verified accounts, versioned batches, durable progress, the pool and the worker. Both work; the newer one is where the recent effort went.
- **Mismatched version metadata.** The package metadata still lists Python 3.7–3.10, while the pool and worker refuse any Telethon other than 1.45.0.
- **Live tests are rare.** Most verification is by offline tests that simulate Telegram's replies. Live tests against Telegram exist, but depend on a logged-in account.

## Who would use it and why

Anyone who needs to collect what is said in many Telegram groups over time, reliably and without getting their accounts restricted:
- researchers and analysts;
- data pipelines feeding other systems;
- services that watch groups for listings or announcements.

The careful parts — allowances, health events, verified identities, replayable batches — are aimed at running many accounts for a long time, unattended.

## Its general shape

A Python package (`tgdata`) with one main entry class (`TgData`), an account-pool class (`AccountPool`), a login flow (`LoginFlow`), and a set of focused engines underneath for connections, messages, batches, discovery, sync, backfill and health. Every connection to Telegram is built in one place, which applies the proxy, device identity, session storage and allowance guards. The two commands are `tgdata-login` and `tgdata-worker`. There is no web interface or server of its own.
