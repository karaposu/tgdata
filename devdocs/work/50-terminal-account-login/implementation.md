---
model: gpt-6-astra
effort: xhigh
---
# #50 implementation under revision 8

Archive product: eb1f564. Product-only PR head: b1d9dcc.
Base remains dev77f2f53. The user authorized implementation with “continue” after
the complete prebuild passed. Prior implementation/verification are preserved in
implementation_r4.md and verification_r4.md; both rejected PR critiques remain
historical evidence, not clearance for this revision.

## What changed

The CLI uses a private byte-observable terminal reader for every hidden value and
confirmation. It retains at most128 UTF-8 bytes, permanently invalidates oversized
or unsupported-control lines, and discards the remainder through Enter/EOF/stop.
Erase/clear cannot turn a rejected suffix into a credential. Unsupported terminal
profiles refuse before mutation/source work. Input is admitted only after exact
terminal restoration and owned-fd retirement have succeeded.

SIGINT records stop without raising into input restoration. The intermediate
canonical transition retains the active protected controls: echo, extended/flow
processing and quit/suspend remain disabled until the final original-mode write.
A failure retains separate primary-operation and cleanup facts and releases no value.
The existing one-action cancellation driver, LoginFlow and native publisher remain.

## Qualification and promotion

- Fresh plan critic81598e2 found one Medium in intermediate control restoration.
  Its real native probe showed SIGQUIT could be delivered while echo remained off.
- Fold70d32cf selected the robust active-profile restoration sequence in revision8.
- Full prebuild PASS b0caa03 was committed before the first product edit. One complete
  run covered every retained and new history and the isolated installed command.
- Both promoted product modules match the exact passing candidate bytes. The native
  publisher is unchanged. verification-r8/promotion.json records hashes/adaptations.
- Permanent smoke48 retains23 groups and adds3 matrix groups:70 terminal/profile
  cases,46 framing histories and7 real SDK/native-file handoffs. Four test-only
  helpers keep producers, fault injection and observations out of product code.
- Public docs define the128-byte limit, hidden confirmations, supported editing,
  irreversible invalid-line discard, per-prompt invitation and truthful cleanup.

No design deviation or product correction occurred during implementation. Harness
packaging changes replace candidate loaders with product imports, use portable
paths, remove work-folder result writes, invoke the actual product module and import
the installed suite in the installation probe.21 retained test functions have
identical ASTs; the argument-redaction test was renamed and the module-entry test
now invokes the product module. All qualified helper assertions are retained.
The outer smoke48 verification allowance is240 seconds instead of120 because it
now includes all three native matrices; case deadlines remain unchanged, and a
killed process is never counted as success.

The plan changes the obsolete getpass seam: observable hidden-input/refusal native
coverage replaces its fallback unit test. The qualified small-canonical-limit case
now succeeds because byte streaming does not depend on the kernel canonical limit.
Persistent restoration faults continue to report failure, with fixture repair kept
separate from product success. These decisions were established before promotion.

## Verification and handoff

See verification.md and verification-r8/ for actual run results. Renewed merge
check and fresh in-session PR critique remain pending. PR51 stays draft; no merge,
release, live Telegram login, environment deployment or ScrapeOps change.

Current-thread model/effort metadata verifies gpt-6-astra/xhigh for this continuation;
see model-verification-r8.md. No subagent. Version remains0.1.1; no dependency/export
change. Original checkout/version edit, duncan, unrelated guides and #45/PR49 stay
separate. Native3.7, other hosts and live delivery/real-account2FA are not qualified.
