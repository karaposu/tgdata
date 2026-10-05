# Concept map — message-batch territory

Goal: Implement a stable producer contract for message snapshots, safe continuation and content-hashed media that can be replayed independently of a future worker.

## wire-record

Canonical name: Versioned message representation
Status: live
Own manifestations: `docarchive/sensemaking.md#A1`, `docarchive/decomposition.md#P1`, `docarchive/critique.md#P1-F`
Own-depth pointer: none
Depth-signal: Exact optional field depth — [mid] — the implementation must have a concrete schema.
Individuation: matched manifestations by shared referent and goal role; kept distinct where the role differs.
First-seen: 2026-10-05T11:24:02.773350+00:00
Last-touched: 2026-10-05T11:24:02.773350+00:00

## snapshot-identity

Canonical name: Stable snapshot identity
Status: live
Own manifestations: `docarchive/sensemaking.md#A2`, `docarchive/innovation.md#P1-F`
Own-depth pointer: none
Depth-signal: Canonical byte grammar — [mid] — digest reproducibility needs an explicit encoding.
Individuation: matched manifestations by shared referent and goal role; kept distinct where the role differs.
First-seen: 2026-10-05T11:24:02.773350+00:00
Last-touched: 2026-10-05T11:24:02.773350+00:00

## continuation

Canonical name: Completed-prefix continuation
Status: live
Own manifestations: `docarchive/sensemaking.md#A3`, `docarchive/decomposition.md#P3`, `docarchive/critique.md#P3-F`
Own-depth pointer: none
Depth-signal: Concept framed; no separate depth record.
Individuation: matched manifestations by shared referent and goal role; kept distinct where the role differs.
First-seen: 2026-10-05T11:24:02.773350+00:00
Last-touched: 2026-10-05T11:24:02.773350+00:00

## blob-publication

Canonical name: Verified content-addressed media
Status: live
Own manifestations: `docarchive/innovation.md#P2-F`, `docarchive/critique.md#P2-F`, `../probe_batch_seams.py`
Own-depth pointer: none
Depth-signal: Concept framed; no separate depth record.
Individuation: matched manifestations by shared referent and goal role; kept distinct where the role differs.
First-seen: 2026-10-05T11:24:02.773350+00:00
Last-touched: 2026-10-05T11:24:02.773350+00:00

## media-mode

Canonical name: Media eligibility and download mode
Status: live
Own manifestations: `docarchive/sensemaking.md#A3`, `docarchive/decomposition.md#P3`, `docarchive/innovation.md#P3-F`
Own-depth pointer: none
Depth-signal: Concept framed; no separate depth record.
Individuation: matched manifestations by shared referent and goal role; kept distinct where the role differs.
First-seen: 2026-10-05T11:24:02.773350+00:00
Last-touched: 2026-10-05T11:24:02.773350+00:00

## guarded-reads

Canonical name: Shared quota and health behavior
Status: live
Own manifestations: `docarchive/decomposition.md#P3`, `docarchive/critique.md#D4`
Own-depth pointer: none
Depth-signal: Concept framed; no separate depth record.
Individuation: matched manifestations by shared referent and goal role; kept distinct where the role differs.
First-seen: 2026-10-05T11:24:02.773350+00:00
Last-touched: 2026-10-05T11:24:02.773350+00:00

## legacy-compatibility

Canonical name: Existing API compatibility
Status: live
Own manifestations: `docarchive/sensemaking.md#Phase-4`, `docarchive/critique.md#P3-C`
Own-depth pointer: none
Depth-signal: Concept framed; no separate depth record.
Individuation: matched manifestations by shared referent and goal role; kept distinct where the role differs.
First-seen: 2026-10-05T11:24:02.773350+00:00
Last-touched: 2026-10-05T11:24:02.773350+00:00

## delivery-obligation

Canonical name: Replay and acknowledgment obligations
Status: live
Own manifestations: `docarchive/sensemaking.md#A5`, `docarchive/critique.md#P4-F`
Own-depth pointer: none
Depth-signal: Concept framed; no separate depth record.
Individuation: matched manifestations by shared referent and goal role; kept distinct where the role differs.
First-seen: 2026-10-05T11:24:02.773350+00:00
Last-touched: 2026-10-05T11:24:02.773350+00:00

## sdk-grounding

Canonical name: Telethon 1.45.0 contract evidence
Status: live
Own manifestations: `_branch.md#User-Steering`, `docarchive/critique.md#External-evidence`, `../probe_batch_seams.py`
Own-depth pointer: none
Depth-signal: Concept framed; no separate depth record.
Individuation: matched manifestations by shared referent and goal role; kept distinct where the role differs.
First-seen: 2026-10-05T11:24:02.773350+00:00
Last-touched: 2026-10-05T11:24:02.773350+00:00

## schema-evolution

Canonical name: Version acceptance and evolution rules
Status: live
Own manifestations: `docarchive/decomposition.md#P1`, `docarchive/innovation.md#P1-F`
Own-depth pointer: none
Depth-signal: Concept framed; no separate depth record.
Individuation: matched manifestations by shared referent and goal role; kept distinct where the role differs.
First-seen: 2026-10-05T11:24:02.773350+00:00
Last-touched: 2026-10-05T11:24:02.773350+00:00

## bounded-work

Canonical name: Bounded read and file-processing work
Status: live
Own manifestations: `docarchive/sensemaking.md#Resource-feasibility`, `docarchive/decomposition.md#P3`
Own-depth pointer: none
Depth-signal: Exact limit and I/O scheduling policy — [mid] — resource behavior must be concrete before implementation.
Individuation: matched manifestations by shared referent and goal role; kept distinct where the role differs.
First-seen: 2026-10-05T11:24:02.773350+00:00
Last-touched: 2026-10-05T11:24:02.773350+00:00

## shared-scanner

Canonical name: Generalized scanner for multiple formats
Status: live
Own manifestations: `docarchive/innovation.md#P3-G`, `docarchive/critique.md#P3-G`
Own-depth pointer: none
Depth-signal: Concept framed; no separate depth record.
Individuation: matched manifestations by shared referent and goal role; kept distinct where the role differs.
First-seen: 2026-10-05T11:24:02.773350+00:00
Last-touched: 2026-10-05T11:24:02.773350+00:00

## ack-stream

Canonical name: Acknowledgment-aware worker streaming
Status: live
Own manifestations: `docarchive/innovation.md#P4-C`, `docarchive/critique.md#P4-C`
Own-depth pointer: none
Depth-signal: Concept framed; no separate depth record.
Individuation: matched manifestations by shared referent and goal role; kept distinct where the role differs.
First-seen: 2026-10-05T11:24:02.773350+00:00
Last-touched: 2026-10-05T11:24:02.773350+00:00

## Invocation log

- 2026-10-05T11:24:02.773350+00:00: fresh breadth survey of this territory and goal; 13 live identities recorded; no prior entries or stale identities.
