---
model: gpt-6-astra
effort: max
---
# Triage — #7 Stage3 group lookup and access

**Weight:** feature-heavy. **Path:** feature. **Priority:** P2.
**Surfaced:**27 tagged source/contract/SDK items in surfacing.md; the verified-client
and owned-health boundaries, read-budget admission, typed group/cache identities,
metadata and invite shapes, public exports/docs/dependencies and real-SDK tests.
**Why heavy:** the new public result is consumed by callers and owned-health recovery;
metadata, membership and readable history are distinct observations. SDK resolution,
local caches, account identity and budget admission must agree without false denials
or recoveries. Failures can otherwise look like plausible readiness results.
**Watch for:** copying old broad #7 code/assumptions, inferring origin from a native
exception class, inferring read access from membership/preview, creating a second
ownership system, broad dialog sweeps, and accidental join/login operations.

## Warmth

Same session as Stage1 and Stage2 implementation, review and merge. Base30ba706 is
the branch ancestor. Full factory, Stage1, health/owned-health, budget, session and
facade implementations are retained from that work; current models/SDK group shapes,
get_entity, public exports/dependencies, batch/group resolution seams and old PR16
rejection were refreshed. No archaeology refresh is claimed. Retained model/effort:
gpt-6-astra/max, latest previously recorded turn2026-10-07T05:34:50.039Z.

## Traverse decision

Required under CONTRIBUTING §5: Stage3 creates a public group-observation contract
that later joining can consume, and connects concrete access evidence to Stage2's
explicit semantic recovery assertion. Run a bounded inquiry on what each result
may claim and which failures must remain errors. The ownership/lifetime architecture
is already merged; the inquiry must not reopen it without new contradictory evidence.

## Boundaries and pipeline

Lookup/access only; no joining, join allowance, routing, storage backend, scheduler,
legacy health migration or live Telegram action. Current SDK is1.45.0 layer229;
official method pages are semantic references, not a substitute for the installed
schema. Package metadata still advertises1.33 while requirements is unbounded; the
supported-version statement must be considered explicitly by description/planning.
No known external blocker for the offline work. #7 is reused, not duplicated.
Stage3 has no parked description and no PR rejection. Prior distinct stage/whole-
issue critiques remain references, not three retries of this new stage.
