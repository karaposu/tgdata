---
model: unknown
effort: unknown
---

# Merge check — issue #5

Reviewed in the implementation session on 2026-10-05, against `origin/dev`
at `110996c` and the feature through `7a2f549`. Inputs: triage, description,
plan revision 2, the original critic, implementation record and actual diff.

**Implementation-to-plan check: complete. Ready to open the PR, subject to the
separate PR critic. This is not merge authorization.** The maintainer requested
an explicit go-ahead before merging. The model-rule exception below also needs
their disposition before merge.

## 0. Session warmth and weight

The original warming commit `110996c` and continuation commit `0162acd` are
ancestors of this feature. The continuation read all 41 existing Python source
files, including the unfinished session class, before implementing. The task
documents and relevant Telethon 1.45.0 lifecycle code were also read. This is
recorded in `desc.md`; the small summary was refreshed in `75a518a`.

Triage classifies this feature-heavy; GitHub #5 has the `heavy` and
`enhancement` labels. The feature crosses the account's login, the session
cache, client construction and application storage, and a failed save can be
noticed only after a restart. The weight remains appropriate.

## 0b. Scope against triage

Runtime changes are confined to the two surfaced constructors/factory and the
new session class described in the plan. Tests and user documentation are the
planned additions. The new test exercises the existing client paths rather
than introducing a second factory. No dependencies or package exports change.

Work-folder artifacts and the archaeology summary are branch records. They
must be excluded when integrating into `dev`, in accordance with §7.6. The
unrelated local `devdocs/guides/group_discovery.md` edit is not committed and is
absent from the PR diff.

## 1. Implementation compared with the plan

1. `StoredSession` keeps login/data-centre state, update states, groups and
   channels, and own identity rows. It excludes response users other than the
   account itself, stores an opaque string, sorts mixed rows safely, checks
   the stored login before changed saves, logs failures without payloads,
   implements optional deletion, and clones into memory.
2. `session_store=None` is appended to both constructors and passed through
   the shared factory. With no store, the same original name reaches Telethon.
   Existing login decisions, pool naming, device probe and health identity stay
   on their existing paths.
3. README and constructor documentation cover the contract. `7a2f549` supplies
   the maintainer's SQLite-table example; the smoke-test README has test_17.
4. Twelve offline test groups cover the specified scenarios. The login stand-in
   follows test_15's technique but is local to test_17, avoiding shared mutable
   module state and that test's import-time temporary-directory creation.
5. Compilation and the six requested suites pass in their offline modes.
   Code/tests/user docs are in `a0e0779`, the later requested README refinement
   is `7a2f549`, and work-folder records are separate in `75a518a` and this
   documentation checkpoint.

One implementation refinement is documented: permissive base64 decoding could
turn a corrupt nonempty key into an empty key. The final decoder validates
both base64 layers and the 256-byte key length, and suppresses parse-error
chaining. This directly enforces revision 2's failed-load requirement; it
does not change the stored format or interface.

## 2. Does the plan still fit the implementation?

The existing Telethon session abstraction and the single client factory remain
the right integration points. The default-file regression suites support the
claim that callers without a store retain their behavior. The SQLite example
also exercises the documented store contract across database reopen.

The check-before-save guard is deliberately not atomic across processes. The
README makes this boundary explicit, matching the unselected compare-and-set
proposal in the original critic. A live Telegram restoration is still
unverified. These are not represented as guarantees established by fake replies.
The forthcoming PR critique separately judges lifecycle soundness and the
adequacy of these boundaries.

## 3. Original critic findings

- Medium 1, sender-cache growth: `_entity_to_row` excludes other `User` rows;
  the test feeds 500 senders and verifies only the group and own rows survive.
- Medium 2, credential logging: save/delete errors log the session name and
  exception type only. The failure test injects payload-bearing store errors
  and checks all captured records, including traceback fields.
- Medium 3, stale login overwrite: changed saves compare the current stored
  key to the last synchronized key. Tests cover a first-login race, replaced
  key, removed record, and same-key last-writer behavior. Cross-process atomic
  compare-and-set was consciously left outside the interface.
- Medium 4, mixed-row sorting: rows sort by JSON text. A public/private pair
  survives restoration, with deterministic dumps.
- Low 5: synchronous event-loop cost is documented.
- Low 6: an opaque base64 envelope prevents storage layers interpreting large
  access hashes as JSON numbers; the exact signed 64-bit value is tested.
- Low 7 remains accepted: the two saves inside real Telethon `connect()` were
  read, not exercised by the new offline suite. Disconnect and auth-key saves
  do run through Telethon's real code.

## 4. Issue status and verification

The original issue request is preserved. Steps T and 0–4 remain checked against
their existing committed artifacts. Step 5 is checked against the published
implementation, SQLite example and verification record. Steps 6 and 7 remain
unchecked until their artifacts are committed and the PR actions actually
happen. No merge or closure is recorded in advance.

Verification: 65 executed offline checks passed; 3 live checks were deliberately
skipped. Test_12's five offline/loopback checks passed after localhost access
was enabled. The existing test_12/test_13 banners count skipped checks as
successes; the implementation record separates them. Changed Python files
compile and whitespace checks pass. The exact README SQLite class passes a
temporary-database save/reopen/restore/delete probe.

## §9 model rule — maintainer attention required

CONTRIBUTING assigns feature work to **Fable 5.1 at max** or **GPT 6 Astra at
xhigh**. The inherited plan/critic frontmatter instead records
`claude-opus-5-5[1m]` at `max`. This session identifies itself as Codex/GPT-6,
but its exact model variant and effort are not exposed; they are recorded as
`unknown`, not inferred to be Astra/xhigh. The rule's satisfaction cannot be
certified. The maintainer must decide whether to accept these artifacts or
require review in the prescribed model before approving merge. This flag is
separate from the code-risk verdict and must not be presented as resolved by
passing tests.
