---
model: unknown
effort: unknown
---

# Merge check — issue #9

**Fidelity verdict: PASS.** The implemented diff follows folded plan revision 2.
This is not the fresh PR soundness verdict or authorization to merge.
CONTRIBUTING §9 model/effort compliance cannot be certified; see the process
qualification below. PR critique remains required after opening the PR.

Reviewed in the same warmed session on 2026-10-05. Subject:
`origin/dev` at `af593fc2fb146b4e14334b96c472c8dade78652a` through
`3f554449a0667949c448c6135bc173e456c2d11f`; runtime commit `07d983a`.
Remote references were refreshed and matched these commits. Read together:
`triage.md`, `desc.md`, `step_by_step_impl_plan.md` revision 2, `critic.md`,
`implementation.md`, and every changed runtime/test/documentation file.
`step_by_step_impl_plan.md` is this branch's authoritative plan filename.

## 0 — Warmth and weight

The description records the full codebase read and #5 implementation/review/
merged-tree verification at `af593fc`, plus Telethon request and iterator
source reads and pre-build probes. That commit is an ancestor of this branch
and is still the current remote `dev`. The session remains warm across this
review; no subagent was used.

Triage at `8c76e38` calls this feature-heavy: identity, durable quota state,
actual dispatch and multiple readers interact, and an accounting failure can
be silent. GitHub #9 currently has `enhancement` and `heavy`, matching the
record. Its decision that traverse was unnecessary is explicit and checked,
not omitted.

## 0b — Scope against triage

Existing changed runtime files are the surfaced connection factory, message
engine, discovery engine and TgData façade. README was surfaced as the public
contract. New `read_budget.py`, `budget_client.py` and `test_18_read_budget.py`
implement the quota/dispatch/test concepts triage identified as absent.
`tgdata/__init__.py` and the smoke-test README were not separate triage rows;
they are export and discoverability work specified by plan steps 3 and 5,
not additional runtime concepts. The heavy classification remains appropriate.

The work-folder files are preparation, probe and verification artifacts. They
stay on the feature branch at integration. The unrelated working-tree edit
to `devdocs/guides/group_discovery.md` is absent from the committed diff; its
SHA-256 still matches the implementation record.

## 1 — Implementation versus plan

- **Step 1:** `ReadBudget` implements the file-backed SQLite policy/charge
  schema, atomic `BEGIN IMMEDIATE` claims, rolling expiry, warm-up, persisted
  clock high-water, explicit reconfiguration, token settlement, status and
  local exceptions. It stores no credentials or message contents.
- **Step 2:** `BudgetClientMixin` classifies supported bounded reads and
  wrappers, refuses unsupported message requests/batches, guards the real
  sender argument inside the SDK request loop, and wraps page/ID iteration.
  `_new_client` attaches the same ledger for primary, pool and ephemeral use.
- **Step 3:** the trailing constructor option and exports are additive.
  `get_read_budget()` avoids connection when disabled. Engines preserve
  processed partial output; polling delivers its partial frame before
  propagating exhaustion and treats other local budget errors as terminal.
- **Step 4:** 28 behavioral groups exercise real SQLite and SDK control flow,
  including concurrency, identity, retries, cursors, failures and partials.
- **Step 5:** the README and smoke-test entry explain configuration, counts,
  excluded traffic, identity lookups, clock/storage behavior and limitations.
- **Step 6:** implementation/report commits are separate, all prescribed
  offline checks passed, and live checks were explicitly excluded.

No design deviation is hidden in the diff. The two fixture corrections during
verification are recorded in the code commit and implementation report:
MessageEmpty's required peer, and the older SDK's low-ID end-of-history
heuristic. Neither changed product behavior or weakened quota assertions.

## 2 — Does the plan still hold?

Yes as the implemented contract: admission before each application-level send
is the common boundary for all selected readers, and a separate transactional
ledger supplies atomic coordination that the session store's load/save API
does not. Charging returned protocol slots before presentation prevents
filters from making reads free. Temporary page sizing and unchanged raw ID
vectors preserve their different semantics. Optional wiring retains existing
default behavior.

The actual contract is narrower than an unrestricted reading of "whoever is
calling" in the original issue. This was already selected in the description
and issue status: budget-enabled tgdata clients sharing one local database;
explicit pulls, not metadata previews/passive updates/file bytes; no sandbox
against private transport bypass. The docs preserve those boundaries rather
than claiming universal protection.

Scripted responses establish client-side enforcement, not live Telegram bounds
or safe rates. The plan explicitly keeps that server premise unverified and
requires charging/stopping on oversized replies. The fresh PR critic must
still attack correctness independently of this fidelity check.

## 3 — Pre-implementation critic closure

The sole Medium finding was cached identity being used as billing authority.
The selected robust proposal is present in `BudgetClientMixin._read_budget_account`
and `_BudgetSender.send`: read the authenticated self response for each attempt,
then reserve and enqueue without another await. Page sizing and public status
use the same helper; retries re-enter it. A hidden logout triggers GetState to
preserve Telegram's real error. SDK identity cache is not cleared or trusted.

Tests establish cached 111 versus authenticated 222, changed identity between
page sizing and send, no message dispatch for missing policy/logout, and
correct health reporting. The pre-build critic's High/Medium findings are all
answered. It contained no Low findings. Its unselected wider account-lifecycle
proposal remains a future consideration for #8, not an unclosed prerequisite.

## 4 — Issue status and evidence

GitHub #9 is open. Its original request is preserved. Current completed
checkpoints map to commits: triage `8c76e38`, description `eeb86a7`, plan
`4a0951a`, critic `b3f44e2`, fold `c88ac47`, implementation `07d983a`, and report
`3f55444`. Traverse is checked with its documented "not needed" reason.
Steps 6 and 7 are correctly unchecked when this check is written; step 6 may
be ticked after this artifact is committed and the PR exists, and step 7 only
after the fresh critique is committed and posted. No box claims a merge.

Verification is 95 offline groups in the main Telethon 1.45.0 environment,
plus 28 budget groups on isolated Telethon 1.33.1 and the README example.
Three live proxy/device checks were skipped, not counted as live passes.
The code tree has not changed since those checks. Diff whitespace check passes.

## Process qualification and integration constraints

CONTRIBUTING §9 assigns new feature work to Fable 5.1/max or GPT 6 Astra/xhigh.
The exact active variant and effort are not exposed here; every artifact
records `unknown`. This gate flags the discrepancy and does **not** certify
that requirement. The user has authorized this review/PR work with that
limitation previously recorded. Any eventual merge decision must retain it.

Open the PR into `dev` with `Closes #9`, post this check, then run critic-d on
the diff and revision-2 plan in this session. Any High or Medium rejects it
under §7.3 and requires re-planning under §7.4. Merge remains a separate user
decision. At integration, exclude this work folder, retain the branch as the
archive, run checks on the merged code, and close #9 manually if GitHub does
not close it for a merge into `dev`.
