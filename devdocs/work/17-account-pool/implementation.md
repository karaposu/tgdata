# Implementation record — #17

**Product:** `964d082` on `feat/17-account-pool`, based on dev95ed4c7.
**Result:** requested offline delivery implemented; verification.md records 393 passes.

| Plan step | Result |
|---|---|
| 1 values/state | account_pool.py values/errors; pool_state.py strict opaque CAS state and SQLite adapter |
| 2 owned source | pool_source.py; additive factory and opt-in BatchEngine resolver/cancellation hooks |
| 3 routing | bounded drain/spread; exact admission/settlement; source-prefix/error preservation |
| 4 lifecycle | local status/enrollment; credential reload; explicit recovery; quiescent cleanup |
| 5 progress facade | shared delegators; original TgData constructor and module-local factory seam retained |
| 6 offline histories | test31, 36 groups; actual SDK/SQLite, overlap, lost replies and owned process exits |
| 7 usage | README, docs/account_pool.md, related docs and isolated runnable example |
| 8 verification/commit | 393 checks; 3 examples; 66 files compile/grammar; isolated build; product commit complete |
| 9 live gate | pending by confirmed user choice: one account, offline first |

Selected critic mitigations implemented: source-body outcome retention precedes
health observer work; recheck retires/reloads the stored credential before its new
identity attempt. Formal pre-build experiment passed before product changes.

No #7 code or work artifacts were adopted. The main checkout remains paused on
feat/7-group-operations. Its pre-existing HANDOFF and the user's local todo.md remain
outside this feature commit. No duncan or stray group-discovery guide edit was staged.

Public errors/records contain type/reason metadata, not credential values or source
message text. Actual receiver data stays caller-owned. Opaque pool state records
account source permission; it neither grants quota nor owns group acknowledgment.

## Next review boundary

Perform the formal CONTRIBUTING merge-check against triage/description/folded plan/
critic and product diff. Then publish a code-only PR into dev and run a fresh PR
critic in this warmed session. Those steps are pending; no review verdict is inferred
from implementation tests. Keep the live gate visibly pending unless real resources
and authorization are supplied. Merge still requires the user's go-ahead.
