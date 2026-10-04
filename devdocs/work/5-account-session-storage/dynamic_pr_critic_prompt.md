# PR critic prompt — issue #5, PR #13

Use ultrathink. Review the implemented diff against `origin/dev` together with
plan revision 2, the description, triage, original critic, and merge check.
The review runs in this warmed session, not a subagent. Preserve the original
`critic.md` and `dynamic_critic_prompt.md`; write this review to `pr-critic.md`.

Read the session adapter, every client construction/login/close path, the
health identity, cache consumers, the new tests and relevant Telethon 1.45.0
implementations in full. Judge the final behavior rather than comments or test
names. The store contract remains synchronous load/save with optional delete;
encryption, migration and shipped backends remain out of scope.

Probe these lifecycle boundaries with synthetic credentials and no network:

1. Restore through Telethon's real client, including its real connect-time
   handling of the own-user rows and update state where affordable. Distinguish
   scripted server replies from actual Telethon behavior and live Telegram.
2. Exercise save, close and log-out after another client replaced or removed
   the stored login. Does every mutating path honor the lifecycle promise?
3. Check malformed payloads and storage failures across construction and save:
   first-login decisions, error type, chaining and credential exposure.
4. Confirm that side-session clones never save into the account store, and
   that omitted stores retain the default file behavior and proxy/device paths.
5. Check the scope of cached identities, large integers, deterministic mixed
   rows, and the real SQLite example across a restart. Examine costs without
   inventing scalability claims.

Classify the non-atomic load/save window as the already documented boundary;
do not rediscover it as a new finding without a distinct contract violation.
The two connect-time saves were a consciously accepted Low in the plan, and
live Telegram restoration remains unverified. Existing disclosure is not proof
of safety: new lifecycle failures require their own evidence and severity.

Write frontmatter `model` and `effort` from exposed session metadata, using
`unknown` when unavailable. Then give one of IMPLEMENT AS WRITTEN, IMPLEMENT
AFTER FOLDING THESE IN, REORDER — TEST BEFORE BUILD, or DO NOT IMPLEMENT —
MEANING GAP/WRONG LAYER, followed by the falsifier and its affordability. Add a
separate PR verdict: any High or Medium rejects under CONTRIBUTING §7.3.

Include a high-level summary, a premise inventory ranked by wasted work,
restart check, inherited lessons and exact probe results. Each risk has a plain
paragraph, precise paragraph, severity, category, impact, NoobEng and affected
areas. Medium/High findings need quick, robust and long-term proposals, including
why robust/long-term work. Initially leave selected/elegant/last_resort boxes
unchecked and notes empty; then run Phase 3 to select by reach versus extent.
Only report real findings backed by code or a probe. Keep the §9 model-rule
exception separate from the code verdict. Rejection starts a re-plan; it is not
permission to apply individual patches to this PR.
