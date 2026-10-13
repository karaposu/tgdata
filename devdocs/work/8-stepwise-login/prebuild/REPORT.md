# Full #8 prebuild result

**PASS — 23/23 test groups**, Python3.11.10 / Telethon1.45.0, 2026-10-14.
`full-result.txt` is the complete final run; `manifest.json` binds candidate, test,
runner and extracted factory source. Runtime sources were unchanged for this gate.

The isolated candidate uses the repository's real configured factory and all its
mixins, with precisely the planned private base-class parameter. The real SDK runs
connect, raw request serialization, migration, update/save-on-disconnect and actual
SRP computation. An independent synthetic server calculation verifies its SRP proof.
The existing StoredSession produces/loads the credential and the real ordinary
client factory consumes it. Only transport/service replies are supplied by the wire;
socket calls and console input are blocked. This is no evidence of live Telegram
delivery, SMS availability, real password acceptance or physical proxy exit IP.

## What ran
Both no-password and password paths restore between completed calls. The suite also
covers wrong inputs, waits, expired/unsupported challenges, SentCodeSuccess and
password-setup flags, settings/device binding, native DC migration, queued and repeated
cancellation, an interrupted native transport close, known auth/challenge retention,
failed cleanup/refusal/retry, component cancellation, uncertain-result checks without
resending, self mismatch, original session-file isolation, explicit save retry,
malformed secret checkpoints, health isolation and actual native SDK diagnostics.

## Corrections, recorded rather than hidden
- Attempt1:0/22 reached behavior; the wire fixture called AuthKey() without the
  required None argument. Corrected that test-fixture constructor. A diagnostic rerun
  of the unchanged source confirmed the same fixture line/type; no product premise
  was exercised by those failures.
- Attempt2:21/22. All authentication/state/serialization paths passed. The migration
  cancellation case observed two sender-close attempts instead of one. Both settled;
  no escaped work or lost credential was observed. This was a candidate completion
  reuse defect, not the experiment's state/lifetime feasibility falsifier.
- Attempt3:21/22, same assertion. Merely keeping the public close completion was
  insufficient. Source trace corrected the critic's call-site account: Telethon's
  `_switch_dc` awaits private `_disconnect`, not public `disconnect`. The candidate
  now retains that actual transport completion too, and the complete public flush.
  This implements the selected one-owner rule at the missed native call site.
  The test's original assertion is unchanged.
- Attempt4:22/22 with both actual completion boundaries owned. This was not the final
  gate because inspection exposed an untested diagnostic detail: Logger.getChild()
  registers global children even for an unregistered private parent. A local logger
  override returns the same disabled instance for SDK child requests. Added an actual
  ServerError warning-path test with distinctive synthetic secrets.
- Final attempt:23/23, full combined run including that native diagnostic path.

None of the named disqualifying observations occurred: the SDK composition can retain
observed progress/key/DC, restore both inputs, settle its owned work and return a real
consumer-loadable credential. Corrections were a fixture argument, missing native
call-site ownership and SDK logger-child routing; no state contract, API scope or
storage design changed. No failing assertion was relaxed or removed. Old run logs
and manifests remain alongside the final result.

## Next gate
Copy the qualified candidate/tests to the runtime, apply the exact factory seam,
verify source parity and run focused plus the full supported suite. Offline PASS
does not mark live provider qualification complete.
