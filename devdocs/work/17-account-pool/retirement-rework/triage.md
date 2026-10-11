---
model: gpt-6-astra
effort: max
---
# Triage — #17 retirement and current-dev integration

**Weight:** feature-heavy, continuing unmerged#17. The concrete defect is in its
source lifecycle; there is no separately landable pool fix on dev before#17 lands.
Reuse its existing native `feat/17-account-pool` branch and parent issue rather than
filing a duplicate issue. Original implementation/plan records remain intact.

**Surfaced:**18 items in surfacing.md: current pool source/controller/state/progress,
SDK disconnect and #7 cleanup precedent, actual reproduction, client-factory/constructor
integration, original selected mitigations, tests/public contract and process gates.
**Why heavy:** caller cancellation and SDK cleanup have different lifetimes; early
reuse can race session writes/connection teardown. Shared-factory integration and
the original progress-facade extraction also need full regression coverage.
**Watch for:** only shielding an await while releasing the owning operation;
treating failed closure as permission to reuse/reload; misclassifying SDK-internal
cancellation as caller cancellation; losing original source outcomes or repaired
credentials; erasing new dev APIs during conflict resolution.

## Warmth and base

Same session as #7's five stages/review/merge and the immediately preceding #17
assessment. Branch base for this continuation is8d3db76; integration target is
dev68f6bbd. Complete pool modules/test31 and relevant SDK/factory/#7 lifetime,
health, ledger and progress contracts were read or retained at named resolutions.
Both old and disposable combined-tree reproduction showed the retirement race.
The trial sweep passed608 checks, failed only an obsolete signature assertion,
and skipped3 live checks; it is not the future implementation's verification.
No archaeology refresh is claimed. Current session metadata confirms Astra/max,
turn context2026-10-11T07:30:51.596Z, satisfying §9.

## Traverse decision

No new traverse required. The original#17 inquiry already established the owned,
single-process client/state/progress split. The intended retirement contract already
requires actual cleanup before reuse; one-by-one SDK inspection and a deterministic
probe have identified its precise violation. This work repairs that lifetime inside
the existing structure and adapts a factory seam now supplied by dev. It does not
invent a new permission model, credential-generation protocol or generic health
layer. Carry the original inquiry and selected outcome/credential lessons forward.
If planning exposes an unsettled structural choice, revisit this determination.

## Scope and gates

The user's follow-up authorizes focused rework and current-dev compatibility while
keeping the router, budgets, saved restrictions, restart and acknowledgment behavior.
No automatic joining, new scheduler, distributed ownership or broader #7 rewrite.
Run desc → plan → fresh critic → fold/required experiments → implement → verify.
No PARKED marker or rejected PR critic exists. The parent two-account live gate
remains pending; it is not required to perform this offline repair. Review/PR/merge
remain later gates. Preserve original checkout/untracked files, duncan and guide.
