---
model: unknown
effort: unknown
---

# Merge check — issue #5, round 2

**Fidelity verdict: PASS for revision 4 and runtime commit `46aef9c`.**
Reviewed in-session on 2026-10-05 against `origin/dev` at `110996c`, triage,
description, regenerated plan, both plan critiques and the first PR critique.
The independent second PR critique follows this checkpoint. Merge still needs
the maintainer's explicit go-ahead and disposition of the §9 exception below.

The first merge check is retained at `24ddeb8`. The first PR review rejected
`a0e0779` for stale logout deleting a replacement login (`a6deab7`). The task
was re-planned (`cc665f4`), critiqued (`c663b4c`), folded as revision 4
(`ab91f87`), and implemented (`46aef9c`). It did not bypass §7.4 with an
unplanned patch.

## 0. Warmth and weight

The warming ancestors `110996c` and `0162acd` remain on the branch. The
continuation read all 41 then-existing Python files and relevant Telethon
1.45.0 lifecycle implementations. The review subsequently read real connect,
logout, disconnect and entity-cache code and ran probes. `desc.md` records
this, and `75a518a` contains the refreshed small summary.

Triage says feature-heavy and GitHub #5 has the matching `heavy` and
`enhancement` labels. The rejected lifecycle defect confirms that weight:
credential loss can be delayed until a restart.

## 0b. Scope against triage

Runtime changes remain in the planned session adapter and two surfaced
constructor/factory files. The second implementation changes only the adapter,
its tests and user documentation. No dependency, backend, migration, encryption
layer, separate factory or new public operation was introduced.

The SQLite README class is an example supplied at the maintainer's request,
not a shipped backend. Work-folder artifacts/probes and the archaeology
refresh are branch-only records to exclude from integration under §7.6.
The unrelated working-tree guide edit remains uncommitted and outside the PR.

## 1. Final implementation compared with revision 4

- Step 1: description criterion 7 now covers overwriting and deleting another
  login. The real-logout regression failed on the previous implementation
  (`Passed: 11/12`, stale replacement changed) before the runtime edit.
- Step 2: `_may_mutate()` compares the current stored key with `_synced_key`.
  Both changed save and optional delete call it inside their own error
  handlers. Rejections warn once and do not change synchronization markers.
  Ordinary logout still deletes; failed checks retain the record. Unchanged
  saves still return before loading the store.
- Step 3: module/README wording describes conditional deletion, the SQLite
  example is retained, and smoke-test coverage includes stale logout and
  unreadable current records. The original rejected review is archived.
- Step 4: the requested six suites were rerun after the refactor. All 65
  executed offline test groups passed; 3 live checks were skipped. The
  lifecycle probe and exact SQLite example passed on the final code.

Initial implementation refinements remain justified: strict base64 and
256-byte-key validation enforce failed-load protection; test_17 uses its own
small test_15-style stand-in rather than importing test_15's mutable fixture.
The SQLite refinement required a separate documentation commit after the
initial implementation; code/user docs and process notes remain separated.
No further structural deviation from revision 4 was found.

## 2. Does the plan still fit what was built?

One session adapter at the shared factory remains sufficient. The refactor
makes ownership a shared rule for both persistent mutations, matching the
actual Telethon logout order. It does not alter file sessions or login-prompt
policy. The real-connect probe also confirms local restoration of own identity
and update positions and both connect-time save points.

The guard is intentionally a check followed by a mutation, not atomic backend
compare-and-set. Live Telegram acceptance remains unverified. The tests and
probes distinguish those boundaries from local Telethon behavior; the README
does not claim cross-process atomicity.

## 3. Were the critic findings answered?

Original plan critic (`cf7a745`, preserved in history):
- Medium 1: other message senders are excluded; 500-sender test retains only
  the group and own identity rows.
- Medium 2: save/delete failures log name and type, with no error payload or
  traceback. Both original failure cases and new ownership-read failures are
  checked.
- Medium 3: stale saves preserve the changed/removed stored login. Revision 4
  extends that rule to deletion after the fresh PR finding.
- Medium 4: mixed public/private cache rows sort deterministically and restore.
- Lows 5 and 6: synchronous event-loop cost and opaque string handling are
  documented; exact large access hashes survive.
- Low 7: the new archival probe now exercises both actual connect-time saves.
  This improves the evidence; the probe is not part of the routine smoke suite.

First PR critic (`a6deab7`): its sole Medium is addressed by the shared guard.
P4 now reports that no store delete is issued and the replacement login is
preserved. Ordinary deletion, first-login races, removal, failed loads and
corrupt current records are covered. The revision-3 plan critique found no
additional risks to fold.

## 4. Issue status and verification

The original request remains intact. GitHub #5's plan/critic/fold/implementation
boxes now reference `cc665f4`, `c663b4c`, `ab91f87` and `46aef9c`. Final merge
check and PR critique boxes remain pending until those artifacts are committed
and posted; the first rejected review is explicitly recorded. They will be
completed only with their actual review references. No merge or closure is
recorded in advance.

Telethon 1.45.0 / Python 3.11.10: test_17 12/12; test_16 21/21; test_15 11/11;
test_14 11/11; test_13 five passed and one live skip; test_12 five passed and
two live skips. Missing temporary config paths disable live checks. Proxy
checks used localhost only. Changed files compile; whitespace checks pass.

The final lifecycle probe reports: both real connect saves pass; own identity
and update positions restore; stale disconnect preserves the replacement;
stale logout issues zero store deletes and preserves the replacement. The
exact README SQLite class also passed real stale logout across two database
connections, reopen, exact key restoration, and owned deletion.

## §9 model rule — maintainer disposition required

CONTRIBUTING assigns feature work to **Fable 5.1 at max** or **GPT 6 Astra at
xhigh**. The inherited plan/critic record `claude-opus-5-5[1m]` at `max`.
This session is identified as Codex/GPT-6, but its exact model variant and
effort are not exposed and are recorded as unknown. Compliance cannot be
certified. The maintainer must either accept this exception or require review
with the prescribed model before approving merge. Passing code tests and
critique do not resolve this separate process requirement.
