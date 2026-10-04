---
model: unknown
effort: unknown
---

**Verdict: IMPLEMENT AS WRITTEN**

Falsifier: a live Telegram connection refuses the restored login while the
same key/data-centre pair from a file session is accepted.
Affordable now: no — requires a live logged-in account; the approved scope
uses synthetic credentials and excludes live Telegram operations.

**PR verdict: PASS — no High or Medium finding remains.** Round 2 reviewed
in this warmed session against `origin/dev` at `110996c`, PR #13 through
`0908ff5`, runtime implementation `46aef9c`, and folded plan revision 4
(`ab91f87`). No subagent was used. This is a code-review verdict, not merge
permission or a certification of §9 model compliance.

The first rejected review remains in `pr-critic-round1.md` and commit
`a6deab7`. Its Medium finding led to a regenerated plan, critique and fold,
not an unplanned patch. This round examines the final adapter, shared factory,
login rules, cache consumers, tests and documentation as a whole.

## High-level summary

The final change uses Telethon's session abstraction at the existing client
factory. File sessions remain the default; a supplied store keeps the complete
restartable state defined by the task. Serialization rejects corrupt login
keys, keeps large integers exact, excludes other message senders, and orders
mixed cache rows deterministically. Clones stay in memory.

The lifecycle defect from round 1 is resolved. Save and delete call the same
ownership check inside their error handlers. Logout of a client holding an
older key preserves the newer stored login. Failed reads/corrupt current data
prevent mutation, without exposing the stored credential in logs. Normal
logout still deletes its own record. The real-logout regression failed on the
prior runtime and passes on this one.

## Premise inventory

1. **A restored credential is accepted by live Telegram.** First dependency:
   the original feature; failure wastes it. No live test is scheduled under
   the approved scope. A live file/store comparison is the decisive test but
   requires account access and authorization. Scripted transports are
   non-covering for server acceptance; this remains an explicit limitation.
2. **The adapter satisfies Telethon's actual client/session lifecycle.** First
   dependency: adapter and factory. The real constructor, disconnect,
   auth-key callback and logout are exercised in test_17. The review probe also
   runs real `connect()`, observing both save points and restoration of own
   identity/update positions. Transport replies and background loops are
   supplied; local Telethon control flow is observed, not supplied.
3. **Every persistent mutation preserves a replacement login.** First
   dependency: revision-4 ownership rule. The failing pre-change regression,
   final real-logout cases and P3/P4 below cover stale save/delete, including
   first login and removal. Failed ownership reads are covered too. The
   exact README SQLite class was exercised across two database connections,
   stale logout and reopen. Cross-process atomicity is explicitly not claimed.
4. **The default path and existing account behavior remain compatible.** First
   dependency: public constructor/factory wiring. The store parameter is
   appended, omitted stores still pass the same string, and all five existing
   regression suites pass in their offline modes. No dependency or exported
   interface changed beyond the optional parameter.

No newly affordable experiment remains scheduled after its dependent work.
The decisive stale-logout failure was observed before revision 3 was written.

## Restart check

Observed failure: an old client's logout removed a newer stored login.
Established mechanism: Telethon disconnected and called guarded save, then
called the previously unguarded session delete. P4 demonstrated it.
Design element: `_may_mutate()` gates both operations, rejects changed or
removed keys, shares the once-only warning, and leaves synchronization markers
unchanged on rejection. Both handlers contain load/parse/mutation errors.

The repair addresses the actual failing layer. The serializer, login-prompt
rules and other account features were not rebuilt to conceal the symptom.

## Inherited lessons and findings disposition

- Original Medium 1, sender growth: response `User` rows are rejected except
  the account's own; the bounded-cache test covers 500 senders and own identity.
- Original Medium 2, credential logging: failure records contain only the name
  and exception type, with no error text or traceback. Corrupt decoding also
  suppresses its underlying exception chain.
- Original Medium 3, stale saves: key ownership is checked before each changed
  write; it now covers deletion too. Same-key cache writes retain their
  specified last-writer behavior.
- Original Medium 4, mixed sorting: JSON ordering handles text/None pairs;
  deterministic restoration is exercised.
- Original Lows 5/6: synchronous event-loop methods and opaque strings are
  documented. Atomic backend operations remain a possible future interface,
  not part of this feature.
- Original Low 7: real connect-time saves are now exercised by the archival
  probe. Routine smoke-suite coverage still uses scripted login decisions;
  neither is presented as a live Telegram login.
- Round-1 PR Medium: resolved in `46aef9c`, with a demonstrated failing-before,
  passing-after regression and real SQLite composition check.

## Final verification and probes

The six suites on the final runtime code executed 65 offline test groups,
all passing. Three live checks were deliberately skipped by giving test_12/13
nonexistent temporary config paths. Localhost-only proxy checks passed with
socket permission. Changed files byte-compile and whitespace checks pass.

The strengthened archival probe now asserts the corrected behavior:

```text
P1 real connect: data-centre save, then auth-key save — passed
P2 real connect: self identity and stored update positions restored — passed
P3 stale real disconnect: newer stored login preserved — passed
P4 stale real log_out: newer stored login removed: False
P4 store.delete calls: 0
P4 newer stored login preserved: True
```

The SQLite example was extracted from README and executed using synthetic
keys with socket connections blocked. Two separate SQLite connections shared
the table; one replaced the stored login, the old Telethon client logged out,
and reopening the database restored the replacement key exactly. Deleting
that currently owned record then succeeded:

```text
README SQLite example + real stale logout: replacement survives database reopen; owned deletion works — passed
```

## Remaining boundaries and Phase 3

No new actionable High/Medium/Low finding was identified. Phase 3 has no new
mitigation proposals to select. Existing boundaries remain: synchronous stores
must be quick; check and mutation are not atomic across processes; live
Telegram restoration is unverified. These are documented scope/verification
limits, not newly discovered defects hidden by the passing verdict.

## Model rule and merge permission

The model exception in `merge-check.md` remains unresolved: §9 names Fable 5.1
max or GPT 6 Astra xhigh for feature work; inherited artifacts name Opus, and
this session does not expose its exact model variant/effort. The maintainer
must accept the exception or request the prescribed-model review. They must
also give the explicit merge go-ahead. Exclude work-folder/archaeology changes
when integrating into dev, keep the feature branch, run the merged-code suites,
push dev, and close #5 manually only after that authorized integration.
