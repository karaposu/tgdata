# Issue 4 — Listing photos don't exist in the output (and two small provenance gaps)

**Status:** ✅ IMPLEMENTED (2026-07-19) — Approach A landed and live-verified: new columns `ChatId`, `MediaType`, `GroupedId`, `MessageLink`; `Username` now null instead of the `"No username"` sentinel; `GroupedId` stored as nullable Int64 (float64 would corrupt album ids > 2^53). Verified against a real album in Анталья продажа недвижимость (5 messages sharing GroupedId 14274286784162722, exact through CSV round-trip).

**Approach B ✅ IMPLEMENTED (2026-07-20)** — but as an **on-demand `download_media(group_id, message_ids, output_dir=None)` method** rather than the doc's original download-during-fetch flag. Rationale: an on-demand method (fetch references cheap → download only kept listings) matches §6 "host photos only as needed; don't bulk-mirror" far better than a fetch-time flag that mirrors every gallery during backfill. It re-fetches the raw Telethon message by id (the object the fetch path hides) and returns `{id: path|bytes|None}`; pass all ids sharing a GroupedId to pull a whole album. Live-verified: the 5-photo CALYPSO album downloaded as 5 real JPEGs (190/82/62/57/63 KB), bytes-mode works, text-only → None, empty list → {}.

**Plus the download-during-fetch flag (2026-07-21)** — `get_messages(..., download_media_to="dir")` does it in ONE call: fetches the messages AND downloads each message's own media into the directory, recording the local path in a new `MediaPath` column (null for text-only). Mirrors the `include_profile_photos` pattern but for the *message's* media. Live-verified: a 12-message pull downloaded all 10 media files (photos + a video) to disk, MediaPath populated, text rows null. **Three media modes now exist:**
1. `download_media_by_id(ids, output_dir=)` — on-demand, specific ids (spec-aligned "as needed").
2. `get_messages(..., download_media_to="dir")` — bulk, during fetch, files on disk (MediaPath column).
3. `get_messages(..., include_media=True)` — bulk, during fetch, bytes in-memory (MediaData column, mirrors include_profile_photos/PhotoData). Live-verified: byte-identical to download_media_by_id, CSV export drops MediaData, a memory heads-up logs at >250 MB.

**Filenames self-identify (2026-07-21):** on-disk downloads (modes 1 & 2) are named `<ChatId>_<MessageId>.<ext>` (Telethon appends the extension to the stem we pass) — traceable to the exact message from the filename alone, unique across groups sharing a folder, and free of the old timestamp `(1)` collisions. Live-verified via deneme2 (`1707717812_182998.mp4`, `1707717812_183019.jpg`) and the download_media_by_id suite.

**Idempotent re-scrape (2026-07-21):** `_download_or_reuse` predicts the extension via `telethon.utils.get_extension` (verified to match the actual download exactly) and does an O(1) `os.path.exists` — if the message's file is already present it is reused, not re-downloaded. So re-scraping the same/overlapping range never creates Telethon's ` (1)` duplicates and never re-fetches bytes (important for the disposable account's rate-limit budget). Live-verified: two consecutive scrapes of the same 10-message window → 7 files both times, no duplicates, unchanged mtimes, identical MediaPath.
**Where it bites:** propertybot's listing records — spec §2.1 requires **"photos — file references from the message"** as a field. Real-estate listings live and die by their photos; a map pin without them is close to worthless.
**Severity:** blocking for the propertybot use case; harmless for pure text analytics.

---

## What the spec needs

Every scraped listing should carry, alongside the text: *does this post have photos, and how do we get at them?* — at minimum a **reference** (enough information to fetch or link the photo later), not necessarily the image files themselves. The spec is deliberate about this: store references, don't bulk-mirror whole galleries (§6).

## What tgdata gives you today

**Nothing.** The output table has no photo column, no "has media" flag, no reference of any kind. A listing posted as eight photos with a caption comes out as… just the caption. There is no way to tell, from the output, that photos were ever attached.

There *is* one photo-related feature — and it's the wrong one, twice over:

- `include_profile_photos=True` downloads the **sender's avatar** — the profile picture of the person posting. Asking for the apartment's photo album and being handed the *real-estate agent's passport photo*.
- It's also **KVKK-unwanted**: the spec's privacy guardrail (§1) says store nothing beyond the public handle and the public message. A person's face photo is exactly the kind of extra personal data it rules out. For propertybot this switch should simply never be turned on.

### A wrinkle worth knowing: albums arrive in pieces

On Telegram, a post with 8 photos isn't one message — it's **8 little messages holding hands** (each carrying one photo, sharing a hidden "we're an album" tag, with the caption usually riding on the first). If we capture photos without capturing the hand-holding tag, one apartment listing shatters into 8 half-empty rows. Since multi-photo posts are *the* standard format for real-estate listings, keeping that album tag is essential for stitching them back into one record.

## The two paper cuts (fix in the same pass)

1. **No `ChatId` / message link per row.** The spec anchors everything — provenance, the "claim your listing" deep-link, the consent-safe reply — on a link to the original message (`t.me/<group>/<message-id>`). Today a row carries only the message number, not *which group it came from*. The caller technically knows (they asked group by group), but the moment rows from 6 groups merge into one table, that knowledge is gone. Each row should carry its group, and ideally a ready-made clickable link.

2. **Missing usernames are stored as the literal text "No username".** When a poster has no public @handle, the table doesn't leave the cell empty — it writes the *words* "No username", which then look like a real handle to any code building poster links or counting posters. Blanks should be blanks; friendly wording belongs at display time, not in the data.

## Why it's like this

tgdata was built for text analytics — who said what, when — where media genuinely doesn't matter, and its output format mirrors an old CSV layout from before the refactor. The avatar-download feature came from that same "analyze the people" angle. Nobody had a photos-first use case until propertybot.

---

## Solution approaches (high level)

### Approach A — Reference columns only *(recommended now)*

Add a few columns to every row, no downloading involved:

- **has media? / what kind?** (photo, album, video, document)
- **the album tag**, so multi-photo listings can be reassembled into one record
- **`ChatId`** (and a prebuilt **`MessageLink`**) for provenance and claim-links
- and store **blank instead of "No username"**

This is the spec's literal ask ("file references"), it's KVKK-clean (no images stored), it's small (~20–40 lines in the one function that shapes each row), and downstream can always fetch an actual image later using the group + message number.

- **Pros:** small, safe, satisfies the spec, no storage/copyright/privacy questions.
- **Cons:** an actual image file still requires a follow-up step when propertybot decides to show thumbnails.

### Approach B — Opt-in download mode *(later, behind a switch)*

An optional "also save the photos to this folder and put the file paths in the row" mode, for whenever propertybot decides to host its own thumbnails. Off by default.

- **Pros:** one-stop convenience when hosting is wanted.
- **Cons:** more moving parts (disk, naming, size limits); §6 explicitly warns against bulk-mirroring galleries; and it slows fetching. Build it when the hosting decision is actually made, not before.

### Approach C — Leave tgdata alone; propertybot re-fetches photos itself *(not recommended)*

The caller could go back to Telegram with raw Telethon calls ("give me message #4711 from group X again, now with media") whenever it wants a photo.

- **Pros:** zero tgdata changes.
- **Cons:** double the requests (rate-limit budget spent twice per listing — see Issue 3), and it forces propertybot to speak raw Telethon — the exact thing using tgdata was meant to avoid. And without at least Approach A's "has media" flag, propertybot can't even know *which* messages are worth re-fetching.

### Recommendation

**A now** — it unblocks the spec with references alone and includes both paper cuts. **B later**, as an off-by-default switch, if/when propertybot chooses to host thumbnails. Skip C. Separately: treat the avatar feature (`include_profile_photos`) as *do-not-use* for propertybot, on KVKK grounds.

## How we'll verify

1. Pull from a real group containing a known multi-photo listing.
2. Assert: the photo rows are flagged with the right kind; all pieces of the album share the same album tag; the caption row is identifiable.
3. Click a generated `MessageLink` — it must open the original message in the Telegram app (test one public-username group and one private group, the link formats differ).
4. Assert no cell anywhere contains the string "No username"; posters without handles have genuinely empty cells.
5. Confirm exports (CSV/JSON) carry the new columns cleanly.

---

## Appendix — exact pointers (for the developer)

- **Row-shaping function (where columns are born):** `tgdata/message_engine.py:224-262` (`_process_message`) — add `msg.photo`/`msg.media` type detection, `msg.grouped_id` (the album tag), and pass through the chat id (already known to `fetch_messages` via the resolved entity).
- **Schema:** `tgdata/models.py:31-56` (`MessageData` + `to_dict`) — new fields: `chat_id`, `media_type`, `grouped_id`, optionally `message_link`; note `to_dict()`'s keys are the de-facto column contract for all downstream code.
- **The sentinel to null out:** `tgdata/message_engine.py:236` (`"No username"`); keep friendly wording in the display formatter (`tgdata/utils.py:15-35`) instead.
- **Link formats:** public group → `https://t.me/<username>/<message_id>`; private/no-username → `https://t.me/c/<internal_id>/<message_id>` (internal id = channel id without the `-100` prefix).
- **The avatar feature to leave off (KVKK):** `tgdata/message_engine.py:251-256` (`include_profile_photos` download block).
- **Exports:** `tgdata/utils.py:38-93` — mirror the existing "strip binary before CSV/JSON" handling if Approach B (downloads) ever lands.
- **Related:** the propertybot requirements this serves: `.../propertybot/devdocs/scrape_needs.md` §2.1 (photos field), §1 (KVKK minimalism), §6 (don't bulk-mirror).
