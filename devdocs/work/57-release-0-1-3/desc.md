---
model: gpt-6-astra
effort: xhigh
---
# Publish the reviewed PENDIN fix as tgdata 0.1.3

## Problem Statement
Released0.1.2 refuses supported native terminals with PENDIN. PR56 corrects that
allowlist and the old refusal test; its full native/offline/fresh review evidence is
committed. The maintainer requests publication, not only a source merge.

## User Value Proposition
A normal package upgrade supplies working terminal login with unchanged input,
authentication/session ownership and cleanup safeguards.

## Success Criteria
Freeze reviewed devaec2592, apply exactly five0.1.2→0.1.3 substitutions (__init__ and
smoke42/43/45/46), qualify every tracked byte, build wheel/sdist and verify exact
payload/metadata/entry points. Full34 offline suites/seven demos and actual isolated
installed PENDIN plain/2FA login plus native-SRP stop must pass before adoption.
Version and promotion PRs pass committed/posted fidelity and fresh soundness reviews.
New annotated v0.1.3 peels to verified main; actual release-event run succeeds and
non-yanked PyPI files pass hashes/payload/fresh isolated installation. Close57 then.

## Scope Boundaries
No new feature, dependency/workflow change, tag reuse, release yank, real Telegram
login or ScrapeOps deployment. Reuse archive/product branches. Work docs stay outside
dev/main. Preserve user edits/other branches. Tests qualify local Darwin/Python3.11.10
and Telethon1.45.0; syntax3.7 checks are not native3.7 or universal-host proof.

## Known Blockers
No OPEN planning blocker. Complete actual candidate qualification gates adoption;
reviewed exact-main provenance and fresh version/tag availability gate publication;
actual workflow/PyPI/install observations gate completion. Existing tools/token name
establish a route, never future publication success. Same warmed session and model.
