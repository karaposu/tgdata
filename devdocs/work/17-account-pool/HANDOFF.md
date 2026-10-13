---
model: gpt-6-astra
effort: max
status: DESCRIPTION_REQUALIFIED_NEW_PLAN_PENDING
---
# #17 — upstream ownership contract saved; implementation remains rejected

The user requested “return to the description/traverse before another plan. , do it”.
That upstream work is complete. No new implementation plan or production patch was
written. PR26 stays draft, unmerged and rejected on the current product `a63099e`.

## Read before continuing

- [New finding](../../inquiries/2026-10-13_11-46__17-public-outcome-ownership/finding.md):
  full sequential Articulate → Surfacing → Sensemaking → Decomposition → Innovation →
  Critique → Routelister, saved with evidence and archived discipline outputs.
- [Description revision5](desc.md): the current requirements. Revision4 is desc_r4.md.
- [PR round2 critique](pr-critic.md): actual rejected implementation, unchanged.
- [Old handoff](HANDOFF_pr_round2.md): exact state before the upstream return.
- Rejected `step_by_step_impl_plan.md` revision5, plan `critic.md`, prebuild_r3.md and
  verification_restart.md remain historical artifacts. Do not resume old folded steps.

## What was missing

The application Task is a stop address, not the lifetime of a tgdata invocation and
not a reliable data envelope. Ordinary shield/gather composition can replace its
cancellation payload even without close. Waiting non-destructively for the whole
Task still waits for unrelated application cleanup after tgdata has returned.

The revised contract separates a private completion fact for actual owned work from
an explicit caller-retained, single-use destination for data. Capturing/retrieving
data is local; true cancellation stays cancellation. Account permission, quota,
progress receipts and acknowledgment remain separate. No new global supervisor,
result database, automatic joining or whole-pool rewrite is justified.

Pool close ends source/control work and retires clients; a public daily/backfill call
can still be publishing progress under its own caller. Its recipient is not final
until that public call ends. Provisional data must never imply final success or a
receipt. Reuse, prestart cancellation, disposal and early retention are explicit
requirements, not features implemented by the small adapter.

## Evidence and limits

- Current product:6 wrapper histories,3 post-call application histories,6 retained
  regression controls observed with actual SDK/SQLite/ReadBudget.
- Isolated concept:46 histories pass, including6 lifetime contrasts,24 genuine
  cancellation deliveries and16 actual provider-fault settlement/publication cases.
- Fresh boundary critique:3 observations pass (daily/backfill publication past close,
  cancellation before coroutine entry). Early-data publication is NOT implemented
  by the exit-only concept adapter.
- First concept probe's eight-turn timing assertion failed; preserved log and corrected
  bounded completion observation are in the inquiry. No data expectation was reduced.
- One full traverse iteration. Upstream answer accepted; stronger cross-SIC convergence
  explicitly unclaimed. All skills ran sequentially in this session, no delegation.
- Sockets blocked; Python3.11.10 / Telethon1.45.0. No live traffic or new native3.7 claim.

## Next authorized phase, when resumed

A new task plan from description revision5, fresh critic-d, fold, then **the full
combined real-component prebuild before production edits**. The plan must qualify
public recipient binding/early retention/finality, actual store phases and uncertainty,
stop provenance, native cleanup, wrappers/observer order, application continuation,
all existing regressions and current-dev integration. Only then implementation,
renewed merge-check and fresh PR critique. No piecemeal patch to the rejected plan.

CONTRIBUTING §7.4's required description/traverse return is now recorded; this does not
reset or erase review history. Exactly two rejected PR rounds and one failed design
prebuild. Current integrated dev is2ddb852; check for newer dev before later design.

E1 still needs two approved accounts/shared group/existing bounded allowance after
offline verification. User selected offline-first. Any merge needs user go-ahead,
excludes work/inquiry/archaeology docs, and keeps the feature branch as the archive.
Main checkout, duncan and unrelated files remain untouched.
