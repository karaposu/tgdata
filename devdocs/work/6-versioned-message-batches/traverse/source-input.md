User invocation: $task-impl on #6 — stable, versioned message batches.

Original issue request:
Filed 2026-10-03 from a draft proposal written for a downstream consumer of tgdata (the proposal itself is not public). The request below keeps its own wording, trimmed to what tgdata itself would do.

**Request.** "Read group X from message N" returns a **versioned batch**:
- the messages, with ids, text, sender, dates and media references;
- an explicit "continue from message M" for next time;
- media files named by a content hash.

The format is the contract between the side that reads and the side that processes. If it's fixed and versioned, either side can change without breaking the other, and a repeated upload is harmless.

**Today.**
- **Reading is resumable, but the output isn't a contract.** `fetch_messages` already continues from a given message id, works in batches and resumes after slow-downs, but it returns a DataFrame.
- `MessageData.to_dict` exists, but no format is fixed or versioned.
- The result doesn't say where to continue next time.
- Downloaded media is named `<chat_id>_<message_id>.<ext>`, not by a content hash, so a repeat upload can't be recognised as a duplicate.

**When it works.** A reader takes 200 new messages, uploads one batch file plus its media, and records "next: from 48213". If the upload is repeated after a network drop, the receiving side sees the same batch and the same media hashes, and nothing is duplicated.
