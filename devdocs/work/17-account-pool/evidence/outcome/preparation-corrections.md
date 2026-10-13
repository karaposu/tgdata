---
model: gpt-6-astra
effort: max
---
# Candidate construction corrections

Initial build stopped before tests: the replacement marker `# Errors` matched both a
module comment and an indented export-list comment in __init__.py. Narrowed it to the
module import context and rebuilt a fresh export. No semantic test ran or changed;
no runtime design decision changed. The exact first build script and export manifest
are preserved here.

Attempt1 completed all new14 groups, prior review8, existing pool46/lifecycle48, workers
33/25 and the other suites/examples; test12 failed only because sandbox disallowed
127.0.0.1 local proxy bind/connect. It is not counted as a pass. Full rerun requires
local loopback access. No Telegram traffic/live config is enabled.

Coverage audit added three explicit groups (provider-refusal recipient state, local
wait/paused state, bounded diagnostic types) and strengthened the early-media stimulus
from a completed text record to a completed real downloaded blob before the next
blocked download. Candidate runtime and prior semantic expectations are unchanged.
The exact first-attempt scripts are preserved under attempt-1/probes/.
