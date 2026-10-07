# Gate D evidence scope

`observations.json` contains the independent SQL/file/trace audit and content-free
worker reports at product `405218e`. All 14 workers reached their expected results;
the earlier prebuild passed separately before implementation. RPC traces count SDK
requests, not low-level MTProto packets/housekeeping. INJECTED local refusals/exits and
health fixtures are distinguished from actual Telegram observations.

Raw batches, message text/senders, receiver databases/files, source oracles, credentials
and the account identity are not published. Private root:
`/private/tmp/tgdata19-gate-d-live-20261007`. The shared budget stayed at the original
Gate A path; no gate copied/reset its authority.

Reproduction scripts live in `../../stage-8-validation/`: gate_d_support.py,
prebuild_probe.py, instrument_checks.py, gate_d_probe.py and audit_gate_d.py.
Default probe help is offline. Running live again requires a new deliberate resource/
allocation decision; existing root allocations and original evidence must not be reused.
This record is a test-composition receipt, not proof of another deployment's guarantees.
