---
model: gpt-6-astra
effort: max
---
# Triage — #7 Stage 1 account operation

**Weight:** feature-heavy, despite the deliberately small scope.
**Surfaced:** ephemeral lifecycle/client factory, fresh-self SDK behavior, read-budget
admission, stored sessions, health observation seams and actual disconnect cancellation.
**Why heavy:** one mistaken ownership or cleanup boundary can affect which account
acts, whether quota is charged and whether a failed/cancelled operation has ended.
**Watch for:** identity inferred from cache, policy applied after authentication,
successful-looking cleanup while an SDK task still runs, and scope growth into health.

## Warmth and scope

Same warmed session as #18/#19 and #17 work, then the read-only #7 reassessment.
Refreshed actual current-dev connection, budget, session and SDK lifecycle sources;
base `95ed4c7` is this branch's ancestor. Architecture documents retained unchanged;
no new architecture-skill run is claimed. Last available same-session turn metadata
reports GPT-6 Astra/max (2026-10-07T05:34:50.039Z); no subagent handoff.

Stage folder has no PARKED marker or prior rejected critique. The parent history
has one unique rejection, so task-impl's three-rejection decomposition guard does
not fire. The user's explicit Stage 1 selection supersedes the old pause for this
scoped foundation only, not the broad revision 3 plan.

## Traverse decision

Required by CONTRIBUTING §5: this is a new operation-ownership boundary that later
group operations will depend on. Keep the inquiry bounded to identity, request
policy, admission agreement and cleanup. Existing #7/#17 evidence can constrain it,
but it must not turn into a new health system or import a pool scheduler.

## Current facts and open design choices

- Existing factory already preserves proxy/device/session settings.
- Fresh get_me may disagree with nonempty cached self ID; budget admission already
  uses a fresh identity. Its optional owned-account check is a narrow integration seam.
- Existing ephemeral authentication runs before the caller receives its client;
  constructor policy must therefore be selected before entering that path.
- Telethon1.45 disconnect shields a child cleanup task. A cancelled awaiting parent
  is not by itself proof of completed cleanup. Probe the real behavior.
- Decide the smallest operation handle/lifetime contract, including behavior after
  scope exit, and precise precedence for primary errors versus cleanup/cancellation.
- Health summary redesign, group operations, joining, database changes and #17
  routing are outside this stage. Offline verification is available immediately.
