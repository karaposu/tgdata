# Gate C evidence

[Gate report](../gate-c.md) is the formal decision. [observations.json](observations.json)
contains sanitized exact observations, not a generated fixture or a replacement for
the assertions in the drivers.

- `audit`: independently read actual saved state/receiver rows, request sums, original
  Gate B hashes and unchanged authoritative policy.
- `prebuild`: unchanged Stage 5 engine with two actual ledgers and real Telegram,
  before building controls; separate from the later product gate.
- `cases`: twelve core worker actions plus the acceptance-matrix supplement, including
  actual source/RPC timestamps, controlled command/receipt orderings and owned exits.
- `oracle`: independent descending history to explicit EOF and direct photo digest.
- `allocations`: nonrefundable per-launch bounds within the total 1,000-slot ceiling.
- `clock_bracket`: host diagnostic only; no monotonic ticks were saved in run state.
- `drivers`: SHA-256 of exact work-folder scripts for reproducibility.

The [core driver](../../stage-6-controls/gate_c_probe.py) prints help unless `--run`
is supplied. It launches only owned sequential workers. The
[matrix supplement](../../stage-6-controls/gate_c_matrix.py) requires its own new
allocation from the same [support module](../../stage-6-controls/gate_support.py).
Reruns must not reuse an allocation or reset either budget. Scripts are scoped to
the approved local setup and are development evidence, not an installed public API.

[Prebuild checks](../../stage-6-controls/prebuild_probe.py),
[instrument checks](../../stage-6-controls/instrument_checks.py) and
[saved-record audit](../../stage-6-controls/audit_gate_c.py) have local-only modes.
The audit's fixed expectations name this recorded run, so a different source view
requires a new independently qualified fixture and evidence rather than silently
changing these assertions.

Raw databases, message bodies, sender data, media bytes, credentials and account ID
remain private. RPC entries publish request types/bounds/times and selected group
message IDs, not request objects or raw error text. Account identity fields are
redacted to `selected-account`. This is one account/source/backend/receiver composition;
future public/deployment behavior still requires Stage 7–8/Gate D and equivalent checks.
