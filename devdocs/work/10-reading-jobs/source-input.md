---
model: gpt-6-astra
effort: max
---
# Source input — #10

## User request

```text
$task-impl |  |  |  |
|---|---|---|
| #10 | Worker process that accepts reading jobs | Not started. Its listed prerequisites—#4, #6 and #7—are now merged. |

do this next after it finishes
```

## Sequence and authorization

#17 review finished first: PR26 is draft/rejected with two Medium findings,
committed at4464021/71502e5 and posted. Its revision3 re-plan is pending; no merge.
The user authorized #10 formal implementation next. Work from current dev68f6bbd,
not the rejected #17 branch. Preserve all other worktrees and the original checkout.

The transport preference question was asked asynchronously: JSON lines stdin/stdout
(recommended subprocess) or HTTP service. No answer received as of this checkpoint;
the stated working default is JSON lines, not an inferred user approval of HTTP.

## Original issue body at intake

Filed 2026-10-03 from a draft proposal written for a downstream consumer of tgdata (the proposal itself is not public). The request below keeps its own wording, trimmed to what tgdata itself would do.

**Request.** Turn tgdata from "a library a script calls" into "a reader that work is sent to": a small worker process that
- holds a set of accounts, with their proxies, sessions and budgets;
- takes jobs: "read group X from N", "check access", "look up this group", "join this group";
- returns batches in the raw format (#6);
- emits health events (#4).

The caller stays the orchestration and processing side. Because it's the same code on a laptop and on a server, an account can move between them. It also draws on #1 (proxies), #5 (session store), #7 (group operations) and #9 (budgets).

**Today.** There's no worker. Callers call tgdata directly, on the machine they run on.

**One thing to keep as it is.** tgdata's connection pool can open **several sessions of the same account at once** (`connection_pool_size`, default 1; each extra connection is its own session file, `<session>_1`, `<session>_2`, …). In the worker, "pool" should mean many accounts with one session each, never one account opened several times.

**When it works.** On a laptop you start the worker once; it shows up as "worker laptop-1: 2 accounts, idle", and starts reading when jobs arrive. On a server the same worker runs with 20 accounts. Moving an account between them is a reassignment plus a re-login through the new proxy.

---
## Pipeline status

**Direction:** blocked — waits for #4 (Report account health states as events), #6 (Return fetched messages as a stable, versioned raw batch), #7 (Look up, check access to, and join groups as short-lived operations) to land first.

**Blocked by:** #4 #6 #7

**Priority:** P3 — backlog: it starts small once its parts exist.

**Path:** feature — new behaviour.
(Labelled `enhancement`; the branch will start `feat/`. Three names, one thing.)

**Weight:** not decided yet. Triage picks `light` or `heavy` after looking at the code — never from this issue's title.

**Branch:** none yet. Create it with:
`gh issue develop <n> --base dev --name feat/<n>-<slug> --checkout`
This repository has only `main` today, so `dev` has to exist before the first branch is cut.

**Docs:** none yet. Everything below lands in `devdocs/work/<n>-<slug>/` on that branch and stays there — devdocs are never merged.

**Session warmth (step W):** not recorded yet. This is a fact about the AI session doing the work, not a command to run. Either it is already warm from earlier work in this codebase — say what it actually read — or it is cold, and `/arch-small-summary` + `/arch-intro` run before anything else. Warming is per session, not per branch. Record which one, at the top of `desc.md`.

- [ ] **T — triage** — `/surfacing` → `triage.md`, then set the weight above
- [ ] **0 — traverse** — only when §5 calls it: `/traverse` → `traverse/`; otherwise tick it with "not needed" and why
- [ ] **1 — desc** — read this issue's body first (§6.1): already structured → adopt it; raw → `/task-desc` → `desc.md`, posted back as a comment
- [ ] **2 — plan** — `/task-plan` → `plan.md`
- [ ] **3 — critic** — `/critic-d` → `critic.md`
- [ ] **4 — fold** — critic's High + Medium into `plan.md` (revision 2, tagged)
- [ ] **5 — implement** — code + tests
- [ ] **6 — merge gate** — `merge-check.md`, then PR
- [ ] **7 — PR critic** — `/critic-d` on the diff → `pr-critic.md`, posted to the PR

**To continue this work:**
1. Check the session is warm — the **Session warmth** line above records how the last one stood. If you are cold, run `/arch-small-summary` and `/arch-intro` first, then update that line to say so.
2. Read `CONTRIBUTING.md` and the project card (`PROJECT_SPECIFICS.md`, not yet written for this repository), then read every file already in the docs folder — the earlier steps changed what this issue is about.
3. Resume at the first unchecked box. Tick each box as its artifact commits.
