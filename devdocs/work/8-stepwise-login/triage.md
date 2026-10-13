---
model: gpt-6-astra
effort: max
---
# Triage — #8 stepwise login

**Weight:** feature-heavy. **Base:** dev c4e6eac89341b204b2749e9d15add578e0706965.
**Branch:** feat/8-stepwise-login, created with gh issue develop and isolated in
/private/tmp/tgdata-8-stepwise-login. No previous desc/PARKED/rejected review exists.

**Warmth:** same session as #17 review/merge and #18 closeout; full factory, session,
operation/lifetime, pool, batch/progress and public consumer context retained. Refreshed
ConnectionEngine, StoredSession, _AccountOperation, config/facade/export seams and
login/store tests against this base, plus installed Telethon1.45 auth/request/connect/
serialization paths. Warm by these reads at ancestor c4e6eac; no redundant archaeology
rewrite claimed. Current turn metadata verifies gpt-6-astra/max, satisfying §9's
feature model family/minimum effort. PROJECT_SPECIFICS.md is absent.

**Surfaced:** [tagged trace](surfacing.md). Public non-console authentication is absent.
Existing headless scraping already refuses unauthenticated sessions without sending
codes; the issue's original persistent-prompt account predates that fix. #1/#5 and
the verified-identity/owned-cleanup foundations are merged. This does not require
the deferred #17 two-account test or an actual proxy exit-IP checker from #3.

**Why heavy:** changes external authentication and credential state across separate
calls. User input, secret serialization, SDK retries/DC migration, cancellation,
session-store publication and independent web consumers meet here. Successful remote
authentication and successful local persistence can differ; failures can be silent.

**Touched territory, to refine in the description:** new login API/controller/value
module(s), existing client-factory seam and session format, public exports, focused
tests, README/usage guide/example. Ordinary readers, worker, account pool, health
storage, quotas and group operations are compatibility controls, not new auth clients.

**Watch for:** sending another code on an automatic retry; returning an old account;
losing a successful remote authorization during later initialization/cleanup; leaking
phone/code/password/auth keys; exporting a Telethon StringSession as though it were
StoredSession's different opaque format; stale/concurrent challenge ownership; a
saved blob implying stronger replay/crash guarantees than it supplies; proxy fallback.

**Traverse required (§5):** new multistep authentication state/ownership structure,
delicately connected to existing credential storage and client lifecycle. Run the
full A→Su→S→D→I→C→R chain before desc. Question: what facts and owners let independent
phone/code/password calls resume safely and produce a reusable session, while keeping
unknown remote outcomes, cancellation and credential publication honest?

**User clarification pending:** whether unfinished login should survive restarts or
move between workers. Options were caller-stored opaque state (recommended) versus
an in-memory first delivery. Keep both readings in the inquiry until resolved; the
API's durability contract must be explicit. No live code request or account change
has been made. Account login setup/resources gate later live qualification only.

**Authorized endpoint:** task-impl preparation, full critique/prebuild as required,
implementation and relevant/full offline verification. Commit completed artifacts at
their checkpoints and product separately from work evidence. PR/merge remain later
gates. Preserve main checkout, untracked HANDOFF/todo and duncan. #17 live validation
stays deferred; this task does not resume it.
