# Stage 1 source input

The user requested task-impl for this stage, following a reassessment of #7:

1. **Declare the expected account.** Use a numeric Telegram account ID, independent of session filenames and cached identity.
2. **Create the temporary client with its policy already configured.** Preserve proxy, device and session settings; configure waits and retries before authentication.
3. **Verify the actual authenticated identity.** A mismatch stops the operation. Missing authentication returns an explicit error without requesting a login code.
4. **Pass that verified identity into the operation.** Later admission checks must agree with it; the operation cannot silently switch owners.
5. **Close reliably.** Cleanup preserves the original result or failure, and cancellation remains cancellation.

The two most important acceptance cases are:

- **Expected B, cached A, authenticated B:** proceed as B.
- **Expected A, authenticated B:** refuse before any group request or join.

## Scope established in the preceding exchange

The user wants stages rather than implementing all of #7. Stage 1 is the single
account/connection boundary. Stage 2 handles health ownership, Stage 3 lookup/access,
Stage 4 join allowance and Stage 5 explicit joining. No new database, multi-account
health registry, group resolver or joining belongs in this stage. No live account
operation has been requested for this coding run.

## History and base

Base: dev `95ed4c76c4d2aba7800d8793b16eb5d54cfba4ec`.
New linked branch: `feat/7-account-operation-foundation`.
Old rejected implementation: `8e245f8`; saved broad revision 3: `8a43d23` on
`feat/7-group-operations`, PR16 draft. They remain historical reference. The old
PR critique has one unique rejection (the archived copy is byte-identical), not
three separate rejected implementations. Neither old product nor revision 3 is
silently imported onto this clean stage branch.

Same-session probes re-established the SDK error exhaustion, stale event/summary
identity and late authentication policy defects. In the latter, default construction
requested a 30-second authentication sleep; constructor-time zero flood threshold
raised the original wait with no sleep. All replies were synthetic; no Telegram
connection or joining occurred.

The unmerged #17 branch offers an explicit-expected-account example, but its pool
state/router is not a dependency of this stage and is not imported as accepted code.
