# Input — #17 focused rework

2026-10-11. The user asked whether the existing account pool needed parts redone or additional logic. Read-only assessment on branch8d3db76 and a disposable combined tree found two integration conflicts and one obsolete constructor assertion;608 offline checks passed, one failed,3 live checks skipped. A separate real-SDK cleanup probe reproduced the retirement/cancellation race on the untouched branch.

The user then explicitly selected the reproduced race:

> An account recheck starts disconnecting its old client. The caller cancels the recheck. The pool accepts another read using that client while its disconnect is still running. ... lets do this

While preparation was running, the user added:

> It needs focused rework, but I wouldn’t start over. The routing, budgets, saved restrictions, restart recovery and daily/backfill integration look reusable. ... lets do this

Authorized continuation: bring existing-access#17 to current dev and correct the source lifecycle while preserving the implemented routing/state/progress mechanisms. Automatic joining is a separate delivery. No live account resources were supplied; the previously confirmed one-account/offline-first constraint persists. This run ends at implemented/verified commits and truthful issue status, with PR/review/merge remaining later gates.

Reuse the existing native feat/17-account-pool branch and parent issue. This is focused continuation of its unmerged feature, not an independently landable fix on dev (which does not contain AccountPool). Preserve original artifacts as the initial delivery's record; current follow-up artifacts live in this subfolder.
