# #8 — source request

User instruction: "Next, as requested: #8—step-by-step login: phone → code → optional 2FA password, without console prompts. Its prerequisite #5 is already merged.\n do this"

The issue was fetched before implementation. Its original request is preserved below;
the older blocked/persistent-prompt status is historical, not the current code's behavior.

Filed 2026-10-03 from a draft proposal written for a downstream consumer of tgdata (the proposal itself is not public). The request below keeps its own wording, trimmed to what tgdata itself would do.

**Request.** A web page can't wait on a console prompt, and Telegram's login is a conversation — number, then code, then maybe a password — where each step arrives as a separate request, often seconds or minutes apart. Three steps, each its own call:
- **start:** "send the code to this number";
- **submit the code;**
- **submit the 2FA password,** if the account has one.

tgdata keeps what Telegram needs between the steps. It returns the finished session, which goes straight into the session store (#5), and every step goes through the account's proxy (#1).

**Today.**
- Login happens only interactively, at connect time.
- In headless runs, `ephemeral_client` raises `AuthRequiredError` instead of hanging and says to run an interactive login once, by hand.
- **The persistent path still prompts.** The long-lived client authenticates with Telethon's interactive `start(phone=…)` (`ConnectionEngine._authenticate`). When the session is no longer authorized and a phone is configured, `start()` sends a login-code request and then waits on the console; a headless process fails on the missing input, and each retry sends another code request. Observed 2026-10-03 in a long-running consumer whose session Telegram had logged out.
- There's no way to do the steps separately.

**When it works.** You enter the phone number and press "send code", type the code from Telegram, type the 2FA password if asked, and the account shows "logged in, through proxy 81.x.x.x". Nobody touches a terminal.

---
## Pipeline status

**Direction:** blocked — waits for #5 (Load and save sessions through a pluggable session store) to land first.

**Blocked by:** #5 (#1 landed in 483ec7d on 2026-10-03)

**Priority:** P3 — backlog: needed for logging accounts in from a web page.

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
