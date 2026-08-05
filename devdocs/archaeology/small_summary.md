# What This Project Is — Plain-Language Summary

*Based entirely on what the code actually does, not on what the documentation claims.*

## In one sentence

This is a **reusable toolkit (a "library") for pulling messages out of Telegram groups and channels** — you log in as yourself, point it at a group you already belong to, and it downloads the messages into a neat table you can save, search, and analyze.

It is called **`tgdata`**, and it's meant to be used by writing small Python programs that call it — not by clicking around in an app.

## What it actually is (the shape of it)

- It's a **software component**, not a finished app. There's no window, no website, no menu. A programmer imports it into their own script and uses its features. Think of it as an engine, not a car.
- It's written in **Python** and packaged so it can be installed and shared (there's setup for publishing it to Python's public package library).
- Under the hood it leans on a well-known, mature tool called **Telethon**, which handles the actual conversation with Telegram's servers. This project wraps that tool in a friendlier, more convenient set of commands.
- It works with the data in the form of **spreadsheet-like tables** (using a popular data-analysis library called pandas), which makes the extracted messages easy to filter, count, and export.
- It labels itself **"Alpha"** — early-stage, still-in-progress software. The version numbers in the code even disagree with each other (one place says `0.0.0`, another says `0.0.1`), which is a small sign of its unfinished state.

## What it currently does (the working parts)

The core message-extraction features look complete and genuinely functional:

- **Log in to Telegram** using your own account credentials (kept in a settings file).
- **List every group and channel** your account can see, along with details like member counts and whether each is a channel or a group.
- **Download messages** from a chosen group — either all of them, the most recent few, only those after a certain point, or only those within a date range. This is the heart of the project.
- **Count messages** in a group without downloading them all.
- **Search** a group for messages containing specific words.
- **Save the results** to common file formats (CSV spreadsheets or JSON).
- **Filter and slice** the downloaded messages — by who sent them, by keyword, or by date.
- **Produce simple statistics** — how many messages, who the most active senders are, how many replies vs. forwards, and even a breakdown of activity by hour of day and day of week.
- **Download sender profile photos** when requested.
- **Show a live progress readout** during long downloads (e.g. "1,200 of 5,000 — 45 messages/sec").
- **Download in chunks ("batches")**, with optional pauses between chunks, and hand each chunk off for immediate processing — useful for very large groups.
- **Cope with Telegram's rate limits** (Telegram temporarily blocks you if you ask for too much too fast). The code detects this and waits it out, with an option to back off gradually.
- **Watch a group for new messages** in two ways: by checking on a schedule ("polling") or by reacting the instant a message arrives ("real-time").
- **Refer to groups by their `@username`**, not just their internal numeric ID — a convenience added recently.
- **Health checks** to confirm the connection to Telegram is alive.

## What it appears to be trying to do (in progress or aspirational)

- **Be a building block for data pipelines.** Internal notes frame this tool as the "Extract" step of a larger data-processing flow (the "E" in ETL) — the idea being that a company or researcher would routinely pull Telegram data into a database or warehouse for analysis. The tool supports this pattern, but the surrounding pipeline is not part of this project; only the extraction piece exists here.

- **Reliable live monitoring is still being wrestled with.** There's a detailed problem write-up describing a real, known bug: when many messages arrive rapidly, the "watch for new messages" feature can **silently skip some and lose them forever**. The code contains added bookkeeping to try to work around this (remembering which messages it has already seen), but the author's own notes trace the root cause to how Telegram itself behaves, and it reads as not fully solved.

- **More ways to log in.** A planning document explores alternatives to the current phone-number login — such as portable login tokens and bot accounts — with pros and cons. These are researched but not yet built; the code today only does phone-number login.

- **Abandoned earlier direction.** A `deprecated/` folder holds notes from an earlier, more elaborate design (a bigger "ETL" framework with batch-processing interfaces). That approach appears to have been dropped in favor of the current, simpler single-class design. So the project has already been through one round of "start over and simplify."

## Who would use this, and why

- **Data analysts and researchers** who want to study public Telegram channels — for example, tracking a cryptocurrency-signals channel (the example code points at a real crypto channel), studying online communities, or gathering text for research.
- **Developers building archives or dashboards** who need a dependable way to keep pulling a group's messages into their own systems on a schedule.
- **Anyone who wants a personal backup** of the discussions in groups they belong to.

In all cases the user must be a **member of the group** and must supply **their own Telegram account** — this reads and archives conversations you already have access to; it is not a way to break into private groups. The code only reads; it never sends messages or changes anything in the groups.

## An honest read on the state of things

- **The core "download messages" functionality is solid and usable.** If someone wants to grab a group's message history into a spreadsheet, this does that job today.
- **The live/real-time monitoring is the weakest area** — there's a documented, acknowledged data-loss bug that the workarounds may not fully fix.
- **It's early-stage and single-author.** Alpha status, conflicting version numbers, and "smoke tests" that are really hands-on demo scripts (they connect to a live account, and when they can't, they print fake sample data rather than genuinely testing the code) all point to a personal/early project rather than a hardened product.

### Things that stand out as concerns (visible directly in the files)

These aren't about how the code runs, but they're plainly present and worth flagging:

- **Live personal credentials are committed into the project.** The settings file contains what look like a real Telegram API key, a real phone number, and an account username. Anyone with a copy of this project has those.
- **Login session files are included too.** These `.session` files are effectively "keep me logged in" tokens for the owner's Telegram account — sensitive material that normally should never be shared or stored in a project.
- **Real harvested data is committed.** There's a spreadsheet of roughly 3,800 messages already scraped from a channel, sitting in the project folder.

None of these break the software, but they represent real privacy/security exposure and are the kind of thing you'd want cleaned up before this project is shared with anyone.
