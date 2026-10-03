# Contributing — the AI contribution guide

**This is an AI-native project.** Nearly every line in this repository was
written by an AI agent working from a written brief, and that is expected to
remain true. This document is therefore not a style guide with some AI notes
bolted on. It is the **operating procedure for AI-authored software**, and it
is binding on every contributor — human or model.

> **If you are an AI agent working in this repository: read this file to the
> end before your first edit, and follow it exactly. It overrides your
> default behaviour.** Two things bind you above all others:
>
> 1. **Warm the session before you do anything** — `/arch-small-summary` and
>    `/arch-intro` (§4.1). A cold session writes confident, specific, wrong
>    claims, and this repository has the scars to prove it.
> 2. **You may not "just fix" something because someone asked you to.** Work
>    enters this codebase through one of two pipelines and no other way. §3
>    tells you what to do when someone asks for an out-of-band fix: you
>    decline, and you open an issue instead.

**This document names no project, host, path or command.** Where it refers to
one by its role — the source tree, the staging host, the test suite —
**the project's `PROJECT_SPECIFICS.md` supplies the value**: that file is the
project card. Read it once at the start; adopting this process elsewhere means
rewriting the card and leaving this file alone.

---

## 0. Requirements — install these before you touch anything

Two of them are **hard requirements**. Work done without them is work the rest
of this document cannot guarantee anything about. The third — the pipeline's
skills — installs in one line whenever a session lacks them (§0.3).

### 0.1 GitHub CLI (`gh`) — required

The whole process is keyed on GitHub issues, and `gh issue develop` is what
creates the native issue↔branch link the pipeline uses as its spine (§6.2). No
`gh`, no process.

**macOS**

```bash
brew install gh
```

**Windows** — any one of these; `winget` ships with Windows 11 and recent 10:

```powershell
winget install --id GitHub.cli
# or:  scoop install gh
# or:  choco install gh
```

**Linux**

```bash
sudo apt install gh          # Debian/Ubuntu — see cli.github.com if your
sudo dnf install gh          # Fedora/RHEL     distro's package is old
```

Then, on every platform:

```bash
gh auth login            # choose SSH or HTTPS; needs the `repo` scope
gh auth status           # confirm before starting
```

If `gh auth status` does not print `repo` among the token scopes, run
`gh auth refresh -s repo` — `gh issue develop` cannot create the linked branch
without it, and the failure looks like a permissions error rather than a
missing scope.

### 0.2 The process guard hook — required

The hook is two files, both committed to the repository so they bind anyone
working in its checkouts: `.claude/settings.json`, shown in full below, and the
script `.claude/hooks/process-guard.sh`, given in full in **Appendix 1**. They
are not a personal preference and should not be removed. **If either file is
missing from a checkout, the hook is not installed — and it must be installed
before any other work,** from the two listings in this document.

**Why a hook rather than a rule.** §11 says it: *"Prefer making a rule
structural over remembering it… When you find yourself writing 'remember to…',
write a check instead."* Two rules in this document are mechanically
checkable, so they are checked rather than trusted.

This is not hypothetical. During the first two branches to use this process,
the author of this guide violated §6.4 within the hour and twice began work
while standing on a trunk branch. Reading a rule does not prevent drifting from
it under momentum; a check at the moment of the act does.

**What it does.** A `PreToolUse` hook on `Bash`, deliberately narrow — anything
it does not recognise passes through untouched:

| trigger | action |
|---|---|
| `git commit` on `dev` or `main` | **blocks** (§8), with an escape for the §3.2 emergency |
| `gh pr create` on a `fix\|feat/<n>-*` branch with no `merge-check.md` | **blocks** (§7) |
| `gh issue create` | reminds: labels, and that the body is the request, not the spec |
| `gh issue develop` | reminds: warm if needed, then triage before planning |

**`.claude/settings.json`** — the whole file:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/process-guard.sh\"",
            "timeout": 10,
            "statusMessage": "Checking the contribution process…"
          }
        ]
      }
    ]
  }
}
```

**Install.** Once both files are committed, a fresh clone has them already.
If they are missing, create them: the settings file from the block above, the
script from Appendix 1. They need `jq` and `git` on `PATH`, and the script
must stay executable.

*macOS / Linux:*

```bash
brew install jq                                  # or: sudo apt install jq
chmod +x .claude/hooks/process-guard.sh          # git preserves this; check after a copy
```

*Windows — read this, the guard is a bash script:*

```powershell
winget install --id jqlang.jq        # or: scoop install jq
winget install --id Git.Git          # Git for Windows — includes Git Bash
```

**Git Bash is required on Windows, not optional.** Claude Code runs command
hooks under bash, *falling back to PowerShell when Git Bash is absent* — and
under PowerShell this script does not run, so the guard is silently inert and
every rule in §7 and §8 goes unenforced with no error to notice. Installing Git
for Windows (which bundles Git Bash) is what makes the hook real there. Verify
after install:

```powershell
bash -c "jq --version && git --version"    # both must print
```

If your `bash` is WSL rather than Git Bash, the hook still works, but the paths
it sees are WSL paths — clone and work inside WSL rather than straddling the
two, or the repo-root lookup resolves somewhere you did not expect.

Claude Code only picks up `.claude/settings.json` for directories that had a
settings file when the session started. **On a fresh clone, open `/hooks` once
or restart the session** — otherwise the hook is present and silently inert.
Verify with `/hooks`; it should list one `PreToolUse` entry on `Bash`.

**The emergency escape.** One *deliberate* bypass exists, for §3.2 only — see
also the unintended one below:

```bash
ALLOW_TRUNK_COMMIT=1 git commit -m "hotfix: …"
```

Reach for it only for §3.2. A documentation-only commit on `dev` needs no
bypass — the guard permits those by rule (§8). That distinction is the point:
an escape hatch used routinely stops working as an alarm.

There is deliberately **no bypass for the merge gate**. If a branch is named
`fix/<n>-…` or `feat/<n>-…` it is pipeline work and needs its `merge-check.md`;
a branch that is genuinely not pipeline work (a one-off docs branch, say)
should not carry that name in the first place.

**A known, unintended bypass: git worktrees.** The guard (Appendix 1) opens with:

```bash
repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
branch="$(git -C "$repo_root" rev-parse --abbrev-ref HEAD 2>/dev/null)" || exit 0
```

That resolves the repository from **the hook's own working directory**, not from
the directory the command will run in. So a command that reaches into a worktree
— `cd <worktree> && git commit`, or `git -C <worktree> commit` — is judged
against the main checkout's branch. With the main checkout on a feature branch
and a worktree on `dev`, a code commit to `dev` passes unchallenged. The same
blind spot affects `changed_paths()` and the `merge-check.md` lookup, which both
read from the wrong tree.

**Left open, deliberately, for now.** Two reasons, neither of them "we forgot":

- The fix means extracting the command's own working directory out of the text
  it was given — a leading `cd`, a `git -C`. That is the kind of parsing that
  makes a narrow guard wide, and this hook's first bug was over-matching on text
  it should have ignored.
- Worktrees are how work *legitimately* reaches `dev`: §7.6's merge recipe runs
  in one, and the guard already carries a `MERGE_HEAD` exception so it does not
  block the sanctioned path. Tightening this carelessly would block the one
  route the process depends on.

**What it changes about how to read the guard.** It was never a security
boundary — the escape variable is documented three paragraphs up, and
anyone who wants past it can walk past it. The difference that matters is
*loudness*. The emergency escape is loud: you type the variable, so you know
what you did and so does the next reader of the history. **The worktree path is
silent** — no prompt, no signal, nothing in the commit to say the rule was not
applied. That is the part worth fixing eventually, and the part to hold in mind
meanwhile: if you are working in a worktree, the guard is not watching, and the
rules in §7 and §8 are yours to keep.

Fixing it is a behaviour change to the guard, so it goes through an issue and a
branch like any other — §8's documentation carve-out deliberately excludes
`.claude/`.

**Its limits, stated plainly.** It checks two things and reminds about two
more. It cannot tell whether the session was warm, whether the critic was
actually folded, or whether the plan is any good — those stay human and
merge-gate judgements. A hook makes the cheap rules unforgettable; it does not
make the expensive ones automatic.

### 0.3 The pipeline skills — install them when a session lacks them

The pipeline's steps (§4) run as skills: `/arch-small-summary` and
`/arch-intro` to warm up, then `/task-desc`, `/task-plan`, `/critic-d`, and
`/task-impl`, which runs desc → plan → critic → fold → implement as one chain.
They live in your home folder, not in this repository, so a fresh machine, a
cloud session or a teammate's setup may not have them.

**If any of them is missing, install the whole AlignCraft command pack with one
line** — before the first pipeline step, not halfway through:

```bash
# For Claude Code
curl -sL https://raw.githubusercontent.com/karaposu/AlignCraft/main/install_claude.sh | bash

# For Codex
curl -sL https://raw.githubusercontent.com/karaposu/AlignCraft/main/install_codex.sh | bash
```

Both write to your home folder only; nothing lands in this repository. The
Claude Code script puts the commands in `~/.claude/commands/`, downloads one
hook script to `~/.claude/hooks/` without switching it on, and gives Claude
Code read access to `~/.claude/skills/` in `~/.claude/settings.json`. If the
commands do not appear, start a new session. The Codex script writes each skill
to `~/.agents/skills/<name>/SKILL.md`, where Codex finds it by itself; there
they are called with `$` instead of `/` (`$task-desc`, `$critic-d`). On
Windows, run the line in Git Bash (§0.2).

**`/surfacing` (triage, §4.3) and `/traverse` (§5) are private skills — not
in the pack.** A session without them does that work by hand, as Appendix 3
describes. When the install itself fails (no network, say), run the missing
step by hand the same way, with `ultrathink` in the prompt. A missing skill is
never permission to skip its step.

---

## 1. Why this process exists — read this part, it is the whole point

The rules below look heavy for a small team. They are not bureaucracy.
Each one exists because of a specific way AI-authored codebases decay, and
every one of those ways has already happened in a real AI-built codebase.

### 1.1 An AI asked to "fix X" will fix X, and damage the system doing it

Given a symptom, a model produces the smallest edit that makes the symptom
disappear. That edit is almost always locally correct and frequently globally
corrosive, because the model cannot see what it did not read. Real examples,
all found in a single audit of an AI-built codebase:

- Five code paths write to one shared resource, and one of them republishes it
  wholesale from a stale copy — so an ordinary edit silently reverts a value
  and destroys data the product had asked the user to supply. No single change
  was wrong. Nobody ever looked at all five together.
- A method was written, tested, and never called. Its own docstring admits it.
  Everything downstream still behaves as though it runs.
- A feature was built correctly, then a later change to the list it depends on
  made it unreachable for **every value a user can actually pick**. Both
  changes were right. The pair is dead code shipped to production.

None of these are coding mistakes. They are **meaning** mistakes — right code,
wrong understanding of the system it lands in. Speed of typing was never the
constraint here. Depth of understanding always was.

### 1.2 The expensive failures were never syntax — they were premises

The costliest work is the work built on a premise that has quietly stopped
being true — a module documented as dormant that live callers still feed, a
measurement taken on one file and generalised to fifteen, a declared
requirement nothing checks. Each is caught by an hour of adversarial reading
**before** the code is written, and by nothing afterwards until production.

That is what the critic step buys. A first plan is always confident and usually
wrong in one specific place. Finding that place costs one prompt; finding it in
production costs a week.

### 1.3 An AI has no memory — the written record *is* the memory

A human engineer carries context between Tuesday and Thursday. A model does
not. It carries nothing at all. Every session begins from zero, reconstructing
intent from whatever is written down.

So in this codebase the artifacts are not documentation *about* the work. They
**are** the institutional memory, and anything not written on the branch does
not exist. This is why the description, the plan and the critic are committed
files rather than chat history: the next model to touch this code inherits
exactly what is in the repository and nothing else.

It is also why this codebase's comments explain *why* rather than *what*, and
cite dates and measurements. Keep writing them that way. When you correct a
comment that has gone stale, that is real work, not tidying.

### 1.4 Human review does not scale to AI output — artifacts do

An agent can produce two thousand reviewed-looking lines in an afternoon. No
human reviews that line by line, and pretending otherwise produces rubber-stamp
approvals, which is worse than no review.

What a human *can* review carefully is a one-page description, a step-by-step
plan, and a critic's list of objections against it. So the review moves
upstream: **we review the thinking, then check that the code matches the
thinking.** That is the only way review stays real at this output rate, and it
is why the merge gate (§7) re-reads the plan against the diff.

### 1.5 Features and bugs fail differently, so they get different pipelines

A bug has a known wrong behaviour: the target is defined, and the work is
locating the cause and fixing it without breaking three other things.

A feature has no defined target. The expensive mistake is not implementing it
badly — it is **implementing the wrong thing well**, because the request was
understood at the level of words instead of meaning. Half the scopes in this
repository's history that were later abandoned or dissolved were built on a
reading of the request nobody had examined.

That is why the meaning comes before the description: the gaps are surfaced
*before* any code is described, while changing your mind is still free — most
often while writing `desc.md` itself, and through the traverse pass (§5) when
the work creates or changes a structure.

---

## 2. The two paths, and there are only two

Every change to this repository is one of exactly two things:

| | **Issue** (a bug) | **Feature** (new behaviour) |
|---|---|---|
| GitHub label | `bug` | `enhancement` |
| Branch prefix | `fix/` | `feat/` |
| Traverse pass | only when §5 calls it — e.g. a bug that step-by-step checking has not cracked | only when §5 calls it — most features build on a structure that exists and need none |
| Pipeline | [traverse →] desc → plan → critic → fold → implement | [traverse →] desc → plan → critic → fold → implement |

There is no third category. "Refactor", "cleanup", "improvement", "quick
change" and "while I'm in here" are not categories — each is either a bug
(something is wrong) or a feature (something new), and you must decide which
before you start. If you genuinely cannot tell, it is a **feature**, because
the ambiguity is itself a meaning gap — to be closed before the description is
written (§5).

**Path is not the whole story.** Every piece of work also carries a *weight* —
`light` or `heavy` — decided after warming and surfacing, not from the issue
title. Path says which pipeline runs; weight says how much system is in play.
The two axes give four kinds of work (issue-light, issue-heavy, feature-light,
feature-heavy), defined in §4.4. Path is chosen when the issue is filed; weight
is chosen at triage (§4.3), because until you have looked, you do not know it.

---

## 3. The rule, and the one narrow exception

**No code is written without an issue and a branch.** Not by a human, not by an
agent, not "just this once."

If someone asks an agent to fix or add something in an ad-hoc way, the correct
response is to **decline the ad-hoc route and offer the pipeline**:

> "That's an issue — let me open it and start the branch."

Then open the issue and begin at §4. This applies no matter how the request
arrives, how urgent it sounds, or how small it looks.

### 3.1 The trivial exception — deliberately hard to qualify for

A change may skip the pipeline **only if every one of these is true**:

1. It changes no behaviour that any test, user, or operator could observe.
2. It touches one file.
3. It is a typo, a comment correction, a dead import, or a formatting fix.
4. It needs no plan to explain, and no reviewer would ask "why?"

Fixing a stale comment qualifies. Changing a default, a threshold, a string
a user sees, or anything inside the application's own source tree, does
**not** — regardless of diff size. A one-character change to a threshold is
not trivial; it is a behaviour change with a measurement behind it.

When in doubt, it is not trivial. Open the issue.

### 3.2 The production emergency exception

Production is broken **now** and users are affected. Fix it on a branch off
`main` (§8), ship it, and then — **the same day, without exception** — open
the issue retroactively, write the description and the plan describing what was
done and why, and back-merge to `dev`. The pipeline is deferred, never skipped.
An emergency that never gets its written record is how the next person inherits
a mystery.

---

## 4. The pipeline

Both paths share a spine. These are slash commands in Claude Code; run them in
this order and commit each artifact as it is produced.

```
                                       ┌ when §5 calls it ┐
issue → branch → WARM UP → TRIAGE  →   │    /traverse     │ → /task-desc → /task-plan → /critic-d → fold → implement → PR → merge gate → PR critic
                                       └──────────────────┘
```

| step | command | output (committed) | what it is for |
|---|---|---|---|
| **W** | **`/arch-small-summary` + `/arch-intro`** | `devdocs/archaeology/` | **warm the session — build a model of the system before touching it** |
| **T** | **`/surfacing`** | **`triage.md`** | **see what this actually touches, then weigh it: light or heavy** |
| 0 | `/traverse` *(only when §5 calls it)* | `traverse/` | work a structure, a delicate join, a changed understanding or a stubborn bug out from every side before anything is described |
| 1 | `/task-desc` | `desc.md` | what and why, success criteria, explicit scope boundaries — **skipped if the issue body already carries them** (§6.1.1) |
| 2 | `/task-plan` | `plan.md` | step-by-step implementation, files named, order stated |
| 3 | `/critic-d` | `critic.md` | adversarial read of the plan, findings ranked by severity |
| 4 | *fold* | `plan.md` (revision 2) | the critic's **High and Medium** findings folded in, each tagged with what it answers |
| 5 | implement | code + tests | the plan, executed — deviations recorded in the commit |
| 6 | PR + merge gate | `merge-check.md` | does the code match the plan, does the plan still make sense |
| 7 | PR critic | `pr-critic.md` | a fresh adversarial read of the diff — any High or Medium rejects the PR (§7.3) |

### 4.1 Warming the session — step W, and it is not optional

**Before any other step, on every branch, run both:**

```
/arch-small-summary        # what this system is and does, from the code
/arch-intro                # the high-level architecture, from the code
```

Then, and only then, start the pipeline. A session that has not been warmed is
**cold**, and a cold session must not write a description, a plan, or code.

**Why this matters more than anything else in this document.**

A model begins every session knowing nothing about this repository. Asked to
work immediately, it does the only thing it can: it searches for strings that
look relevant, reads the fragments around them, and reasons from those
fragments as though they were the system. That produces confident, specific,
wrong claims — and they are wrong in a way that is very hard to catch, because
a fragment of this codebase reads perfectly plausibly on its own.

The characteristic errors are always the same three: a search finds one call
site and misses the wrapper that several live handlers call; a list read as
prose comes out one short; a measurement taken on one file is generalised to
fifteen that were never on the same clock. Each is corrected only by reading
whole files. Warming is how you start from the corrected position instead of
paying for it again.

**A warm session also knows what it must not do.** It knows the product's
locked-out scope, which invariants are enforced at import, how many writers a
shared resource has, and what this codebase's comments are for. None of that
is discoverable from the file you happen to be editing.

**Warming is per session — not per issue, and not per branch.** An agent's
context does not reset when you `git checkout`. If you warmed earlier in this
session, you are still warm on the next branch, and on the one after that; a
session that handles three issues warms once. Re-running the skills on every
branch switch is wasted work and it churns `devdocs/archaeology/` for no reason.

Warm **again** when: the session is new, it was restarted or resumed after a
break, a different agent picked the work up, or the tree moved substantially
under you (a big merge, a long gap since the last warm).

**When you are warm by other means, say so — do not silently skip.** Reading
thirty modules in full during a long session genuinely leaves you warmer than
the skills would; record that in the warming line with what you actually read,
so the merge gate can judge it. What is not acceptable is an unrecorded skip:
"I felt warm" is precisely the self-assessment §1.3 says a model cannot make
reliably.

**Warming is perishable.** The summaries describe the system at a commit. One
from three weeks ago describes a system that no longer exists, which is why the
record below names the commit it was taken at.

### 4.2 Recording the warm-up

Warming produces two committed files — `devdocs/archaeology/small_summary.md`
and `devdocs/archaeology/intro2codebase.md` — which the run refreshes in place.
That is a side benefit: the project's own onboarding docs stay current because
work keeps them current.

The **record** that this branch's work was done warm goes at the top of
`desc.md`:

```markdown
> Session warmed at `1969ec1` (2026-09-04) — /arch-small-summary + /arch-intro.
```

Commit the refreshed archaeology files alongside it if they changed. If they
did not change, say so — an unchanged summary is itself information: it means
nothing structural moved since the last warm session.

The merge gate (§7) checks this line exists and names a commit that is an
ancestor of the branch. **A branch with no warming record does not merge** —
not because the line is valuable in itself, but because its absence means
nobody can tell whether the plan was written by a session that understood the
system or one that was guessing.

### 4.3 Triage — step T, weighing the work before planning it

Immediately after warming, and **before** traverse or the description:

```
/surfacing        # what parts of this system does this issue actually touch?
```

No `/surfacing` in this session? It is a private skill; Appendix 3 says how to
do the same work by reading.

Then classify the work into exactly one of four weights (§4.4) and write
`triage.md` in the work folder.

**Why surfacing comes first, and why triage cannot happen earlier.** Weight is
not a property of the request — it is a property of *what the request touches*,
and nobody knows that from the issue title. "Add a button" is light or heavy
depending entirely on what stands behind the button. So the order is forced:
warm to understand the system, surface to see which parts this reaches, and
only then judge. Guessing the weight from the issue text is how a heavy piece
of work gets planned as a light one, which is the expensive direction to be
wrong in.

When traverse runs (§5), it runs surfacing again as one of its stages.
That is not waste — the two runs have different purposes. Triage surfaces to
answer *"how much system is in play?"*; traverse surfaces to answer *"what does
this request actually mean here?"* The second is deeper and comes after the
meaning question has been opened.

**`triage.md` records four things:**

```markdown
# Triage — issue #43

**Weight:** feature-heavy
**Surfaced:** <the tool definitions>, <the tool handlers>,
              <the view-state module>, <the prompt module>, <the page>
**Why heavy:** the grid is a user-facing surface AND a model-driven one — the
model chooses what appears, so it needs a tool action, view-state
suppression, prompt rules, and a contract for "what is actually visible".
Two consumers, one surface.
**Watch for:** the model claiming an item is on screen when it is not.
```

Then apply the matching label on GitHub, so weight is queryable alongside path:

```bash
gh issue edit 43 --add-label heavy      # or: light
```

**What the weight changes today: nothing.** All four run the same pipeline.
It is recorded now so that when the process does differentiate — and it will —
the decision is made from a body of real classifications rather than from
memory. The one thing it should do immediately is *inform tone*: a heavy
classification tells the critic where to push hardest, and tells the merge gate
how much scepticism the diff deserves.

### 4.4 The four weights

Path (`bug` / `enhancement`) and weight (`light` / `heavy`) are independent
axes, giving four kinds of work.

**Light means all of these are true. Heavy means any one of them fails** — it
is a disjunction, not a score. One heavy criterion is enough, and diff size is
never a criterion at all.

| test | light | heavy |
|---|---|---|
| **Blast radius** | one concept, one seam | crosses two or more concepts |
| **Observability** | if you break it, a test or the screen tells you | failure is silent, delayed, or only visible in production |
| **Consumers** | one thing depends on this surface | two or more, with different needs |
| **Model contact** | the AI neither perceives nor drives it | the AI reads it, reasons about it, or acts on it |
| **Reversibility** | undoable; no money, no records, no user data | irreversible, or touches money, records, or the outside world |

#### issue-light

A wrong behaviour in one place, where being wrong is obvious.

*Example:* a form's back button showed *"connection error"* for any failed
response, hiding the server's real reason, a 409 conflict. One handler, one
file, and you can see it fail.

#### issue-heavy

A bug that crosses seams, **or** one whose wrongness is hard to see — and the
second kind is why diff size is not a criterion.

*Example, and a sharp one:* code read a field through a lookup with a default,
and the field's name was one character off. The default swallowed the mistake,
so an operations dashboard's live-session count showed **zero** for months —
and zero is a plausible number, so nothing ever looked wrong. A one-character
fix, and unambiguously heavy: it fails open, silently, on an operations
surface.

*Example of the crossing kind:* an edit that reverts values and destroys data,
because five separate writers touch one shared resource and one republishes it
wholesale from a stale copy.

#### feature-light

New behaviour confined to one surface, with one consumer, that the model does
not touch.

*Example:* replacing a page's hardcoded identifier with a server-side
resolver — one endpoint, one string in one file, immediately visible.

#### feature-heavy

New behaviour that crosses seams, is delicate, or puts **a second consumer on
a surface that already had one**.

*Example, and the pattern to recognise:* a grid of items. On its face it is
"show four pictures instead of one" — pure UI, obviously light. It was not. The
model chooses what appears, so it needed a tool action, view-state suppression
so it cannot reopen what the user closed, prompt rules distinguishing
*enumerating* from *recommending*, and an explicit contract for what is not
shown, so the assistant never claims something is on screen when it is not.
**A UI that the AI also drives is two systems wearing one surface** — that is
the reliable tell.

*Example of the irreversible kind:* moving an irreversible outside-world action
out of the model's hands — a proposal card, a content fingerprint, a tap that
commits, and an audit row. Heavy on every axis at once.

#### When you cannot decide

**Call it heavy.** The two errors are not symmetric: over-weighting costs some
extra rigour on work that did not need it; under-weighting means a delicate
change was planned as a trivial one, which is the shape of most of the defects
this document's §1 catalogues.

**Step 4 is not optional and not a formality.** The critic ranks its findings
**High / Medium / Low**. The fold takes the **High and Medium** ones —
including the long-term fixes, not only the ones that block implementation —
into `plan.md` as a tagged revision 2, each tagged with the finding it answers.
Low findings are recorded in `critic.md` and consciously left; say so rather
than letting them disappear.

So the plan you implement is the plan that survived attack. A critic run whose
findings were read and not folded is worse than no critic run — it produces the
feeling of rigour without the substance.

**Deviating from the plan during implementation is allowed and normal** — the
plan is a hypothesis and contact with the code refutes parts of it. What is not
allowed is deviating *silently*. Say so in the commit message, and if the
deviation is structural, update `plan.md` in the same commit.

---

### 4.5 When the fix is not the fix

Some problems cannot be solved where they appear. The honest answer is a
**prerequisite**: something built, measured or moved first, after which the real
work becomes possible — or becomes obvious. Weigh this on every issue. Most of
the time the answer is no; when it is yes, it pays for itself many times over.

Four shapes it takes:

- **Instrument it.** You cannot fix what you cannot see. If the failure still
  cannot be described precisely after looking, the first piece of work is the
  measurement, not the patch.
- **Extract it.** If the same fix has to land in five places, the seam is the
  problem and the five sites are symptoms.
- **Build the ground.** A feature with no home gets bolted onto something that
  cannot hold it. Build the home first and the feature turns out to be small.
- **Build the instrument.** Sometimes what is missing is a tool.

**The counterweight matters as much as the principle.** Most issues are exactly
what they look like, and "first we need to refactor" is the oldest way to never
ship. A prerequisite is justified only when it is **smaller and more certain**
than the thing it unblocks. If it is vaguer than the original problem, it is
procrastination wearing a plan's clothes. Four signals that it is real:

1. You cannot state the failure precisely, *after* surfacing. → instrument
2. The same fix would land in three or more places. → extract
3. You have already guessed twice and been wrong. → measure
4. The feature has nowhere to live that would not distort it. → build the ground

**One issue may produce others, and that is a good outcome, not a detour.** When
triage, traverse or the plan turns one up:

```bash
# the prerequisite — a normal issue, ready to pick up
gh issue create --label enhancement --label "open to implement" --title "…"
```

- The prerequisite's body says in one line what it unblocks.
- The parent gains **Blocked by:** `#NN` in its status block, its Direction
  becomes `blocked`, and the `open to implement` label comes off — it is not
  pickable now, and `gh issue list` says so without anyone opening it.
- Record it in a comment on the parent: the checklist tracks progress, and this
  is a discovery (§6.5).
- When the prerequisite merges, the parent returns to `open to implement`.

Do not park the parent's branch half-built while the prerequisite runs. Either
the prerequisite is genuinely first — in which case the parent has no branch yet
— or it is not, and you are doing two things at once.

---

## 5. The traverse pass — when it is needed, and when it is not

Traverse is the heavy pass. It takes a question through several disciplines in
turn — articulating it, surfacing what bears on it, making sense of it,
decomposing it, generating options and critiquing them — and it is built for
questions with several sides that must all hold at once, where a wrong answer
is paid for by everything built on top of it.

**Most work has no such question — most features included.** A new feature
usually builds on a structure or a design that already exists, and its gaps are
small: the AI thinks them through while writing `desc.md` and `plan.md` —
reading the code, deciding what can be decided, and asking the requester what
only they can decide (`/meaning-gaps` sorts the gaps when there are several).
**Do not run traverse, or suggest it, because the work is a feature.**

**Run traverse when the work:**

- **creates a structure, or changes one that later work stands on** — a data
  model, the split between parts of the system, an engine's shape, a page or a
  flow designed from nothing;
- **connects two existing structures in a delicate way** — where each side has
  rules the other must not break;
- **adapts a design to a new method or understanding** — when what the thing
  should and should not be is itself changing;
- **is a bug that checking things one by one has not cracked** — the search has
  turned random, and the whole situation needs a look from every side at once.

**Not needed — though it may still be used — for work inside a structure or a
design that already exists:** a new button on a settled page, a changed label,
an extra column, a link between two tables that already relate. Those details
are within the reach of the description and the plan.

Record the call on the issue either way (§6.5): which of the four the work
meets, or "not needed" and why.

When it runs, its output goes in `traverse/` on the branch and becomes the raw
material for `desc.md`. You are not summarising traverse into the description —
you are writing the description **from a position traverse put you in**.

When the work calls for it, skipping it produces the characteristic failure of
this way of working: a correct, tested, well-reviewed implementation of a shape
that turns out wrong, whose cost appears only as later work is built on it — or
a bug "fixed" at a symptom while its cause keeps moving. Traverse is how you
find that out in an hour instead of a week.

**If the work calls for traverse and `/traverse` is not installed in this
session, do the pass anyway.** It is a private skill — not in the pack in §0.3
— so a fresh machine, a cloud session or a teammate's setup will usually lack
it. Traverse is a discipline, not a tool — its absence is not permission to skip
to `desc.md`. Appendix 3 says how to do the pass without it. The same applies to
any pipeline skill this session lacks and cannot install (§0.3).

---

## 6. GitHub mechanics — issue, branch, docs, PR

### 6.1 Open the issue

Either way works — GitHub assigns the number itself, so nobody tracks a
counter and nobody types a number.

**In the browser** (the usual path — from a phone, mid-service, one sentence):
open the repo → **New issue** → label it `bug` or `enhancement` → submit. Then
hand the agent the address bar, or just say which issue it is.

**From the terminal:**

```bash
gh issue create --label bug          --title "…" --body "…"   # a bug
gh issue create --label enhancement  --title "…" --body "…"   # a feature
```

**Agents: how to pick up an issue you did not create.** `gh issue develop`
accepts a URL as well as a number, so a pasted link is enough and nobody has to
read a number off a screen:

```bash
gh issue list --limit 5      # newest first — find it if you were not given a link
gh issue view 43             # read it before you start
```

If the issue has no label, ask which path it is (§2) before cutting the branch
— the label decides the branch name and the path, and that is not a guess to
make on someone's behalf.

The issue body is a short statement of the problem or the request in the
requester's own words. **A one-line issue is a good issue.** It is *not* the
task description — `desc.md` is, and it comes later, on the branch, after
warming and triage (and traverse, when §5 calls it).

**Give it a priority.** One of `P0`…`P3`, in the Pipeline status block. It is a
guess at this point — made from what it costs to leave the thing undone, not
from how hard it looks — and step 1 confirms or corrects it once someone has
actually looked. Weight already works this way, and for the same reason: until
you have looked, you do not know.

### 6.1.1 Raw issues get qualified at step 1

Filing stays cheap on purpose. §4.5 depends on it — *"one issue may produce
others, and that is a good outcome"* — and an issue that costs a warm session to
file is an issue that gets folded into the current PR instead.

So the structure arrives later, at step 1, where `/task-desc` already runs and
where the session is warm by §4.1. Step 1 begins by reading this issue's body:

- **Already carries `/task-desc`'s five sections** — Problem Statement, User
  Value Proposition, Success Criteria, Scope Boundaries, Priority Level. That
  *is* the description. Adopt it as `desc.md`, revise it if surfacing changed
  something, and tick the box.
- **Raw** — two lines, a screenshot, a sentence from the floor. Run
  `/task-desc` and **post the result as a comment on the issue.**

Five headings or it is raw. The test is mechanical so that two people reading
the same issue reach the same answer.

**The original body is never edited away.** What the requester wrote is
evidence — it is how the failure was actually experienced, and it is the only
account of that not written by someone who has since read the code. Keeping both
is also how the issue shows its own progress: raw, then qualified, in order.

**Qualification may contradict the issue, and should say so plainly when it
does.** A raw report is often a symptom mistaken for a cause — §10.1's wizard
button said *"connection error"* while the server was returning a 409. If
`/task-desc` only reshapes the reporter's words under five headings, it launders
a misdiagnosis into a document that looks investigated. Say what was reported,
then say what is actually happening.

### 6.2 Create the branch from the issue

Always with `gh issue develop`, never `git checkout -b` by hand. This is what
creates GitHub's native issue↔branch link, so the issue page shows the branch
and the PR closes the issue automatically.

```bash
# a bug (issue #42):
gh issue develop 42 --base dev --name fix/42-session-durations --checkout

# a feature (issue #43):
gh issue develop 43 --base dev --name feat/43-dining-area-layout --checkout
```

**Branch naming is fixed:**

| kind | pattern | example |
|---|---|---|
| bug | `fix/<issue>-<slug>` | `fix/42-session-durations` |
| feature | `feat/<issue>-<slug>` | `feat/43-dining-area-layout` |

The prefix says which pipeline ran; the number ties the branch to its issue
without anyone having to remember. Legacy branches (`feat/item-grid`, no
number) predate this and are not retrofitted.

**The slug: three or four words**, hyphenated, chosen once. It is written into
two places at the same time — the branch name and the docs path
`devdocs/work/<n>-<slug>/` — and the issue's status block quotes both, so
renaming it after the first artifact commits means moving a committed
directory and editing the issue. Spend the thirty seconds now.

- **Name the subject, not the verb.** `order-history`, not
  `add-order-history` — `feat/` already means "add".
- **Disambiguate the actor or the surface when the subject alone does not.**
  `owner-order-history` beats `order-history`: two other surfaces show order
  history too, and in six months the branch list is all anyone reads.
- **Never encode the solution.** `order-history-csv` commits to an answer
  nobody has worked out yet, and the name outlives the assumption.

Two words is usually too vague to tell from a sibling issue later; more than
four stops being quotable and gets abbreviated inconsistently.

### 6.3 Post the branch back to the issue

So the work is visible from the issue to anyone who did not create it:

```bash
gh issue comment 42 --body "Branch: \`fix/42-session-durations\` — docs in \`devdocs/work/42-session-durations/\`"
```

### 6.4 Where the artifacts live

On the branch, in one folder named for the issue:

```
devdocs/work/<issue>-<slug>/
├── triage.md     # weight + what surfacing found (§4.3) — written first
├── traverse/     # only when §5 calls it
├── desc.md       # carries the warming record at the top (§4.2)
├── plan.md       # revision 2 after the fold
├── critic.md
├── merge-check.md
└── pr-critic.md  # the merge gate's second check, written after the PR opens (§7.2)
```

Warming itself writes outside this folder — it refreshes
`devdocs/archaeology/small_summary.md` and `intro2codebase.md` in place, and
those go in the same commit when they change.

Commit each as it is produced, not in one lump at the end. The intermediate
states are part of the record — a plan that changed after the critic is more
informative than a plan that looks like it was right first time.

### 6.5 The pipeline status block — the issue says where the work stands

**Every issue carries a status block in its body**, kept current as the work
moves. The artifacts live on the branch; the *state of the pipeline* lives
here, because that is the one place a person or an agent looks first — and
because a session that dies mid-run leaves nothing else saying where it
stopped.

This is §1.3 applied to the process itself. An agent picking the work up
tomorrow has no memory of today. The status block is what it reads instead.

Append this at creation (`gh issue edit <n> --body-file` updates it later; the
original request stays above it). **At creation, nothing is done yet** — that
is the state most issues sit in longest, so it is the one to copy:

```markdown
---
## Pipeline status

**Direction:** open to implement — nothing is in the way; pick it up.
(The other values: `blocked`, which names the issue that must land first
(§4.5); `waiting external input`, which names what is awaited and who provides
it; `parked`, which names what would revive it. If it should not
be built at all, close the issue as *not planned* rather than labelling it —
the open list has to stay readable as the backlog.)

**Priority:** P2 — soon, but not ahead of what is already running.
(Set when the issue is filed, from what it costs to leave the thing undone.
`P0` drop everything; `P1` this cycle; `P2` soon; `P3` backlog. It is a guess at
filing and step 1 confirms or corrects it, the same way triage does for Weight.
It is **not** Direction — a `P0` can sit `parked`, because importance and
readiness are different questions. It is **not** Weight either: `heavy` means
hard, not important.)

**Path:** feature — new behaviour.
(Labelled `enhancement`; the branch will start `feat/`. Three names, one thing.)

**Weight:** not decided yet. Triage picks `light` or `heavy` after looking at
the code — never from this issue's title.

**Branch:** none yet. Create it with:
`gh issue develop <n> --base dev --name feat/<n>-<slug> --checkout`

**Docs:** none yet. Everything below lands in `devdocs/work/<n>-<slug>/` on
that branch and stays there — devdocs are never merged.

**Session warmth (step W):** not recorded yet. This is a fact about the AI
session doing the work, not a command to run. Either it is already warm from
earlier work in this codebase — say what it actually read — or it is cold, and
`/arch-small-summary` + `/arch-intro` run before anything else. Warming is per
session, not per branch. Record which one, at the top of `desc.md`.

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
1. Check the session is warm — the **Session warmth** line above records how
   the last one stood. If you are cold, run `/arch-small-summary` and
   `/arch-intro` first, then update that line to say so.
2. Read `CONTRIBUTING.md` and the project card (`PROJECT_SPECIFICS.md`), then
   read every file already in the docs folder —
   the earlier steps changed what this issue is about.
3. Resume at the first unchecked box. Tick each box as its artifact commits.
```

**For a bug**, the Path line becomes:

```markdown
**Path:** bug — something is wrong.
(Labelled `bug`; the branch will start `fix/`.)
```

**On either path, step 0 says what was decided** rather than being silently
absent. A "not needed" call is ticked — the decision is its record:

```markdown
- [x] **0 — traverse** — not needed: builds on the existing page (§5)
- [ ] **0 — traverse** — called: the bug has resisted step-by-step search (§5)
```

Once the work is under way the seven fields carry real values, and the promise
each label made is kept:

```markdown
**Direction:** open to implement — nothing is in the way; pick it up.
**Priority:** P1 — users hit it on every session, so it costs us daily.
**Path:** bug — something is wrong.
**Weight:** issue-heavy — the server and the client both move.
**Branch:** `fix/2-truncate-on-interrupt`
**Docs:** `devdocs/work/2-truncate-on-interrupt/` (on that branch only)
**Session warmth (step W):** already warm — carried from #9 earlier in this
session; the server, client and record paths read in full. No refresh run.
```

The other honest value, when the session started cold:

```markdown
**Session warmth (step W):** was cold — ran `/arch-small-summary` +
`/arch-intro` at `1969ec1`; both archaeology files refreshed.
```

**Four rules for it.** Tick a box only when its artifact is *committed*, not
when it is written. Never tick ahead. When a step changes what the issue is
about — triage routinely does — say so in a comment, because the body's
checklist records progress, not discoveries. And never let a `§` reference be
the only thing a field says: write what is true now, then point.

### 6.6 Open the PR

```bash
<the test suite>                   # the project card gives the exact command —
<the page-JS suite>                # both have invocation traps worth reading

gh pr create --base dev --fill --body "Closes #42

desc / plan / critic: devdocs/work/42-session-durations/"
```

`Closes #42` is required — it is what closes the issue on merge.

---

## 7. The merge gate — two checks before anything enters `dev`

Nothing reaches `dev` without passing both. They ask different questions and
neither substitutes for the other:

| | asks | artifact | when |
|---|---|---|---|
| **§7.1 merge-check** | does the code match the plan, and does the plan still hold? | `merge-check.md` | before the PR is opened |
| **§7.2 PR critic** | judged fresh, is this code sound in this codebase? | `pr-critic.md` | after the PR is opened |

The first checks **fidelity**: it reads the branch's own documents and asks
whether the diff is what was promised. The second checks **soundness**: it reads
the diff the way a stranger would, owing nothing to the plan that produced it.
A diff can pass the first and fail the second, and that case is the reason the
second exists.

### 7.1 Check one — the merge-check

**Before any PR is merged into `dev`**, an agent — **itself warmed, §4.1; the
gate is a reading job and a cold reader cannot do it** — reads, together:
`desc.md`, `plan.md` (revision 2), `critic.md`, and **the actual diff**. It
then answers four questions in `merge-check.md`, committed to the branch and
posted as a PR comment:

0. **Was the work done warm, and was it weighed?** `desc.md` carries the
   warming record (§4.2) and the commit it names is an ancestor of this branch;
   `triage.md` exists and its weight matches the GitHub label. If the warming
   record is missing, the plan was written by a session that may have been
   guessing, and everything below it is unreliable.
0b. **Did the diff stay inside what triage surfaced?** Files changed that
   `triage.md` never surfaced are not automatically wrong — implementation
   discovers things — but they are the signal that the work was heavier than it
   was weighed. Name them, and say whether the weight should have been heavy.
   This is how the four categories get calibrated by evidence rather than
   opinion.
1. **Does the implementation match the plan?** Every deviation named, with why.
2. **Does the plan still make sense against what the code turned out to be?**
   Implementation teaches things planning cannot. If the plan's reasoning is now
   wrong, say so — a shipped feature whose written rationale is false is worse
   than one with none, because the next reader will trust it.
3. **Did the critic's findings actually get answered?** Every High and Medium
   finding, and where in the diff it is addressed. Lows consciously left are
   named as such.
4. **Is the issue's status block complete and honest?** Every box ticked, and
   each tick backed by a committed artifact.

If any answer is unsatisfactory, the PR does not merge. It goes back a step.

This gate exists because §1.4 is true: nobody re-reads a large diff line by
line, but anyone can check a diff against a plan. It is the step that keeps the
written record honest — without it, the artifacts drift into fiction within a
month and every guarantee in this document quietly becomes decorative.

### 7.2 Check two — the PR critic

Once the PR is open, the merger runs `/critic-d` over **the diff together with
the branch's `plan.md`**, against the codebase it lands in:

```bash
gh pr diff 42 > "$TMPDIR/pr-42.diff"        # or: git diff dev...fix/42-…
/critic-d    # subject: that diff + devdocs/work/42-…/plan.md, in this codebase
```

Say the subject explicitly. `/critic-d` is written to critique a *plan*, and its
first step asks which plan it is; here the subject is the implemented diff and
the plan that produced it. It ranks findings **High / Medium / Low** — the same
vocabulary step 3 used.

**Its output goes to `pr-critic.md`, not `critic.md`.** Step 3 already owns that
filename, and it has to stay as the record of what the plan was attacked with
*before* implementation. Overwrite it and the branch loses the evidence that
step 3 ever ran.

Commit it to the work folder, then post it to the PR:

```bash
gh pr comment 42 --body-file devdocs/work/42-…/pr-critic.md
```

Posting is not optional. The verdict has to live where the merge decision is
made, not only on a branch nobody opens. Note that the guard cannot enforce this
one — it fires on `gh pr create`, and this check happens after the PR exists
(§0.2, "its limits"). Check two is on the merger.

### 7.3 The thresholds

| findings | outcome |
|---|---|
| any **High** | **rejected** |
| any **Medium** | **rejected** |
| **Low** only | merges — the Lows are recorded in `pr-critic.md` and consciously left |

There is no count and no budget. **One Medium rejects the PR.**

This is deliberately stricter than step 3's fold, where Medium findings are
absorbed into the plan and work continues. The asymmetry is the point: at step 3
the code does not exist yet, and a finding costs an edit to a document. Here the
code exists, and a Medium means something different — §7.4.

### 7.4 A rejection regenerates the plan. It does not patch it.

**When the PR critic rejects, the branch does not get its findings fixed one by
one. It goes back to step 2 and re-plans.**

```
/task-plan   → plan.md (revision 3), taking the PR critic's findings as input
/critic-d    → critic.md
   fold      → plan.md revision 4
implement    → the code, again
             → update the same PR; §7.1 and §7.2 both run again
```

That looks wasteful. It is not, for three reasons that compound:

**A Medium here means the first critic missed something.** Step 3 already ran
`/critic-d` against this plan and cleared it to implement. If a fresh read of the
built code now finds a real risk, the thing that failed is not the code — it is
**the context the plan was written from**. Something was not in view. So the plan
is not "sound with three defects"; it is a document whose premises were not what
its author believed they were.

**The plan and the code are coupled.** `plan.md` is the blueprint of exactly what
got built, step for step. Patch the code and the blueprint now describes
something the code no longer is — and by §1.3 the next reader has nothing but
that blueprint. §7.1's question 2 exists to catch this; here we avoid creating it.

**A patch is the worst shape available.** Ask an agent to fix three findings and
it produces three local edits that each make one finding disappear — precisely
the failure §1.1 catalogues. Had those risks been known *before* the plan was
written, the plan would very likely have taken a different and simpler shape.
Re-planning is how you get that shape. Patching guarantees you never see it, and
leaves the three edits sitting on the same premise that produced the risks.

This is the same judgement `/critic-d` already makes one level up. Its third
verdict — **DO NOT IMPLEMENT — MEANING GAP** — deprecates a plan instead of
folding findings into it, on the grounds that folding "produces a patched
document resting on the same hole, and the patching is wasted effort because the
steps change anyway." §7.4 is that verdict applied at merge time, where the hole
shows up in code rather than in prose.

**If the second round is rejected too, stop re-planning.** Two failed gates on
one branch says the problem is upstream of the plan. Go back to `desc.md` — and
to traverse (§5), run now if it was not needed before — because what is wrong is
the reading of the request, not the steps taken from it. Say so in a comment on the issue (§6.5:
the checklist records progress, a comment records a discovery).

### 7.5 Using the skills at this gate

- **`/critic-d` takes the diff *and* `plan.md`.** Given only the diff it produces
  a code review; given both, it can tell a deviation from a decision, which is
  the distinction this gate turns on.
- **`/task-plan` on a re-plan takes `pr-critic.md` as input**, not just
  `desc.md`. Name the revision and say which findings it answers, the same way
  the step-4 fold is tagged.
- **The gate runs in a warm session (§4.1).** It is a reading job, and a cold
  reader cannot do it — that holds for both checks.
- **The merger may be whoever implemented it, and both critics run in the same
  AI session — never in a subagent.** A subagent is not warmed: it starts with
  an empty context and re-reads every file the critique needs, which costs far
  more than the independence it was meant to buy, and it dies with the session
  limit. Independence comes from the critic's rules instead — read the files in
  full, never characterise from a grep, write and run probes for anything that
  rests on behaviour, quote their output, and let a Medium stand only on a
  line of code or a probe. The critique records that it ran in-session; that
  is not a caveat, it is the process.
- **If a pipeline skill is missing, install it first (§0.3); if it cannot be
  installed, run the pass by hand with `ultrathink`** in the prompt — Appendix 3
  shows how for the two private skills. A missing skill is not permission to
  skip a gate.

### 7.6 What merges is the code. The devdocs stay on the branch.

**A PR into `dev` carries code and tests. It does not carry
`devdocs/work/<issue>-<slug>/`, and it does not carry a warming refresh of
`devdocs/archaeology/`.** Those stay on the branch they were written on.

This is why §7.7 keeps branches instead of deleting them: **the branch is the
archive.** The issue links to it, the branch holds the reasoning at the state
it was implemented in, and `dev`'s history stays what it should be — a record
of what the software does, not of how each change was thought about.

Three things follow, and they are the reason for the rule:

- **`dev` does not accumulate process paperwork.** Fifty issues do not put
  fifty `devdocs/work/` folders in the trunk.
- **The archaeology conflict disappears.** Warming rewrites
  `devdocs/archaeology/*`, which every branch shares — two branches warmed on
  different days *would* collide there on every merge. They never meet, because
  neither one merges.
- **The merge gate still reads them.** §7 runs *before* the merge, on the
  branch, where the documents are.

**Mechanically** — keep the docs in their own commits, separate from code
commits, and have the integrator merge with the doc paths excluded:

```bash
git checkout dev && git pull
git merge --no-ff --no-commit fix/2-truncate-on-interrupt
git rm -r --quiet --cached devdocs/work devdocs/archaeology 2>/dev/null
git checkout HEAD -- devdocs/archaeology 2>/dev/null   # keep dev's copy
git commit
```

Refreshing `devdocs/archaeology/` on `dev` is then its own deliberate act, not
a side effect of somebody's feature branch.

### 7.7 Branches are archived, not deleted

After merge, **do not delete the branch.** Under §7.6 the branch is the *only*
place the reasoning exists — `dev` has the merged code and nothing else. A
deleted branch takes the description, the plan, the critic and the merge check
with it, and leaves the issue pointing at nothing.

```bash
git push origin --delete fix/42-…    # ← do NOT do this
```

Leave it. Branch cleanup, if it ever happens, is a deliberate archival pass —
never a routine part of merging.

---

## 8. The branch model

```
fix/42-…  ─┐
           ├─PR──▶ dev ──release──▶ the staging host      (per feature, often)
feat/43-… ─┘        │
                    └──PR──▶ main ──tag──▶ production     (per release, occasionally)
```

| branch | what it is | who sees it |
|---|---|---|
| `fix/*`, `feat/*` | one issue's work, branched **off `dev`** | nobody — it's yours |
| `dev` | the integration line — reviewed work, tested together | the staging host |
| `main` | the prod line — the record of what users run | production |

**Direct pushes to `dev` are not allowed.** `dev` changes only by merged PR.
This is not a preference — a direct push has no diff to check against a plan,
which means §7 cannot run, which means the whole guarantee collapses. If a
change reached `dev` without a PR, nobody can say afterwards what it was for.

**The one carve-out:** a commit confined to `devdocs/` or a top-level `*.md`
may land on `dev` directly — there is no code diff for §7 to check. The moment
it also touches the source tree, the client assets, the deploy directory or
the agent configuration — the project card lists them — it is refused.

**Never commit to `main` directly** either (except a genuine §3.2 emergency).
Main changes by PR from `dev`, and must always describe what users run.

`dev` moves many times a day. `main` moves when a batch is declared ready.
Several pieces of work can accumulate on `dev` across days of staging testing,
then travel to `main` together as one release.

**What may deploy from which branch, and the ways of releasing that fit this
model, are set out in Appendix 2.**

---

## 9. Which model to use

**The most capable model available for the kind of work, at the effort that
kind of work needs.** Not merely the newest — the *biggest*. Those are
different, and confusing them is how a small model gets chosen with a clear
conscience: a small model released this month is still a small model. **Never
Haiku, at any version.** Check with `/model` at the start of a session, and do
not accept a cheaper default because a task "looks small."

As of 2026-09 the assignment goes by the work, and the effort setting is part
of the choice, not a detail:

| work | model and effort |
|---|---|
| **New feature development** — the feature path end to end: triage, traverse when §5 calls it, description, plan, critic, implementation, merge gate | **Fable 5.1 at max effort**, or **GPT 6 Astra at xhigh effort** |
| **Bug fixes and the like** — the bug path end to end, re-plans, PR critics on fixes | **Fable 5.1 at xhigh effort**, or **GPT 6 Astra at high effort** |
| **Analysis and building understanding** — warming, archaeology, reading a subsystem, a finding, an inquiry — and **small bug fixes** (the light bug weight of §4.4) | **Opus 5** |

An artifact's frontmatter records both `model:` and `effort:` so a reader can
weigh it; a critic or a plan produced below the row it belongs to carries that
much less weight, and the merge gate may send it back on that ground alone.

This is an agreement, not a preference, and it holds for every step alike —
triage, traverse, description, plan, critic, implementation, merge gate.

**Why, in the only terms that matter: a smaller model does not save effort, it
defers and multiplies it.** It will produce a fix that works and misses a
delicate mechanism sitting next to it. That miss becomes a bug nobody
attributes to it — which then has to be noticed, filed, triaged, surfaced,
planned, criticised, implemented, reviewed and merged. The whole pipeline runs
a second time for a defect that need not have existed. One cheap session buys
roughly three expensive ones.

The failure mode is worse than slow. This process front-loads its cost into
understanding, and understanding is exactly where capability shows up: a weaker
model produces a plausible plan and a shallow critic, manufacturing the
*appearance* of the rigour this document exists to guarantee. Every artifact is
present, every box ticks, and the gap surfaces in production. §1.4 is why that
does not self-correct — human review does not scale to AI output, so nobody
catches it by reading harder.

The model choice for the product's own runtime LLM calls is a separate
question, governed by the configuration the project card names — do not
confuse the two.

---

## 10. Common pitfalls

Every item below was hit for real — most of them during the first two branches
that used this process. They are listed because knowing a rule and executing it
under momentum are different things.

### 10.1 Process pitfalls

**Merging the devdocs.** The PR carries code and tests; `devdocs/work/` and any
warming refresh stay on the branch (§7.6).

**Deleting the branch after merge.** The docs never merged, so the branch is
the only copy of the reasoning (§7.7).

**Re-warming on every branch switch.** Context survives `git checkout`; warming
is per session, not per branch (§4.1).

**Silently skipping the warm-up because you feel warm.** Record *how* you are
warm — which modules, how much — and let the merge gate judge it. An unrecorded
skip is what §1.3 exists to prevent.

**Writing artifacts without committing them.** Commit each as it is produced
(§6.4). Batching them to the end loses the intermediate states.

**Ticking a status box before its artifact is committed.** A tick is worth
something only if it means something checkable (§6.5).

**Planning from the issue text after triage said otherwise.** Read `triage.md`
before `desc.md` — triage routinely changes what an issue is about.

**Reading the critic and not folding it.** High and Medium findings go into
`plan.md` as a tagged revision 2 (§4 step 4).

**Cutting the branch by hand.** `git checkout -b` gives no issue link and no PR
base default. Use `gh issue develop` (§6.2).

**Branching from `main` instead of `dev`.** `main` is behind `dev` by whatever
has not been released, so the branch sits on a stale base and its diff is
measured against the wrong thing. The exceptions are chosen, not stumbled into:
the §3.2 hotfix, and a deliberate docs-only branch for `main` (see the project card).

**Branching from a stale `dev`.** `git checkout dev && git pull` before
`gh issue develop`.

**Arranging a commit's preconditions in the same command as the commit.** The
guard reads the branch, the merge status and the index as they were when the
command was submitted, so a chained `checkout`, `merge` or `git add` is
invisible to it and the commit is refused. Arrange the state in one call,
commit in the next. Chaining *after* the commit is free.

**Fixing the PR critic's findings one at a time.** A Medium at the merge gate
does not mean the code has three defects — it means the plan's premises were not
what its author believed. Re-plan from step 2; do not patch (§7.4).

**Assuming a label exists.** `gh label list` before `gh issue edit`.

### 10.2 Code pitfalls

**Grep instead of a full read.** Search finds strings, not wrapper functions,
dispatch tables or indirection — and AI-built codebases tend to be dense with
all three. In the audits this process grew out of, every wrong claim came from
a partial read.

**A test that depends on the working tree without saying so.** The suite you
run locally has a `.git` directory, history, tags, and whatever is sitting
untracked. The suite the *release gate* runs has none of that — the release
tool extracts the tag with `git archive` into a temp directory and runs the
suite there,
so the tests see the project's files and nothing else. A test that shells out to
`git`, or reads a path relative to the repository root, behaves differently in
the two places and you will not find out until a deploy. One that shells out
fails outright there; one that needs a tag's contents **skips**, silently, in
the one place it existed for — and a skip is the worse outcome, because a
failure gets read.

If a test genuinely needs the repository, take the path from an environment
variable the release gate can set and make the skip message say which source
it used — a skip has to be true or it is worse than a failure. And see
the project card's release section: run the gate's own context before you
call a release ready.

**A test that reads the source instead of running it.** A string assertion
passes on any file that merely *contains* the substring — including one where
the rule is broken. A test asserting a status code appears in a file is
satisfied by a comment mentioning it; the fix is to extract the rule into
something callable. A test grepping for `try` will bless a handler that has
one and still catches the wrong exception. The string is present and the
defect is intact.

The mirror image is legitimate and worth knowing: when the rule is the
**absence** of a pattern, text is the only instrument, because no amount of
running proves a thing never happens. A test proving that a release script
never re-runs itself (no `exec "$0"` anywhere) has to read the script's text —
and it must strip comment lines first, because a comment may name the
forbidden pattern to explain what the script avoids. Even the right use of a
text test has to separate what executes from what is merely written.
**Absence of a pattern → read the text. What the code does → run it, or
extract it until you can.**

**Trusting a docstring's factual claim.** Comments in an AI-built codebase tend
to be good at *why* and occasionally stale about *what*. In one audit, a
module's docstring claimed nothing fed it, while three live handlers did.
Verify against call sites before repeating.

**`git add -A` without looking.** It sweeps local backup files and scratch
output into the commit. Check `git status` first; stage deliberately.

**Assuming the shell's directory.** The Bash working directory persists between
commands. A `cd src` three commands ago is why your `CONTRIBUTING.md` grep just
came back empty.

**Touching a subsystem that has its own investigation record without reading
it.** Some paths carry months of measured decisions — thresholds, ladders,
routes — where the obvious change has usually already been tried and reverted
with a number attached. The project card names which subsystems these are.

**Editing the process doc on a work branch.** Changes to
`CONTRIBUTING.md` and the project card (`PROJECT_SPECIFICS.md`) belong on the
process branch, not on whatever `fix/*` you happen to be standing in.

## 11. Standards that hold regardless of path

- **Tests land in the same PR as the code.** The test file mirrors the source
  it covers; the project card gives the suites and how to invoke them.
- **Comments explain why, with dates and measurements.** In an AI-built
  codebase the comments are its primary interface, and a comment that has
  quietly stopped being true costs more than a missing one. Correcting a stale
  comment is real work — do it when you find one, and say so in the commit.
- **Prefer making a rule structural over remembering it.** A policy object
  that refuses to import on drift, middleware a route cannot forget, a
  declared-input set asserted against its mirror by test, one home for a
  setting so two doors cannot disagree. When you find yourself writing
  "remember to…", write a check instead.
- **Read files fully before describing what they do.** Grep finds strings; it
  does not find wrapper functions, dispatch tables or indirection. Wrong
  claims come from a partial read or a trusted stale comment, without
  exception. This is the same
  discipline as warming (§4.1), applied file by file: warming gives you the
  system, full reads give you the file, and neither substitutes for the other.

---

<!-- BEGIN EXPERIMENTAL WORKFLOW SCENARIOS -->
## 12. Experimental — discussion, drafts, issues, and implementation

**Trial section, added 2026-09-20.** This section is self-contained so it can
be tested and removed without editing the earlier sections. To remove the
experiment, delete everything between its BEGIN and END markers, including
the markers.

**How it interacts with the earlier rules.** While present, this section takes
precedence only where earlier wording would automatically turn discussion,
investigation, issue capture, or local drafting into pipeline execution,
branch creation, commits, or publication. In particular, the draft/checkpoint
distinction below qualifies "commit each artifact as it is produced" in §§4,
6.4 and 10.1. All other rules still apply: this is not a route around the
implementation pipeline, warming for formal pipeline work, branch protection,
review, testing, or release gates.

### 12.1 The request determines what is authorized

**"Discuss this", "save this", "file this", and "build this" authorize
different things.** Moving between them must follow the user's request, not
an assumption that the next step would be useful. Explicit limits such as
"local only", "don't commit", "don't publish", and "don't implement" take
precedence over automatic progression. If the next action needs authority the
request does not provide, stop at that boundary and ask.

- A **GitHub issue identifies and tracks a task**. Creating one does not mean
  "start building" or approve a proposed solution.
- A **work folder holds that task's documents**. Its existence does not mean
  the documents are approved, committed, published, or ready to implement.
- A **Git commit records a version**. It does not by itself approve a draft,
  publish it to GitHub, merge it, or deploy it.

| Scenario / example request | What the agent should do | Where it stops |
|---|---|---|
| **Discuss an idea:** "What do you think about this?" | Discuss possibilities, trade-offs, and unanswered questions. Read relevant project context when needed. | No automatic files, issue creation, commits, or implementation. |
| **Investigate a problem:** "Why does this happen?" | Inspect relevant code and evidence; explain the cause, uncertainty, and possible fixes. Use non-mutating checks within the request's scope. | Diagnosis is not permission to implement a fix or create an issue. |
| **Save an idea locally:** "Write down what we discussed; I'm not ready to create an issue." | Save clearly marked draft notes under `devdocs/inquiries/<date-and-topic>/`. Record open questions without pretending they are settled. | No GitHub issue, commit, or implementation unless requested. |
| **Prepare an issue:** "Draft an issue for this so I can review it." | Present a proposed title, description, labels, and priority. Keep unresolved questions visible. | Show the draft; do not publish it. Save a file only if requested. |
| **Create an issue:** "Put this on GitHub for later." | Create the issue, preserve the original request, and record its actual readiness. A short request is enough (§6.1). | Do not automatically create an implementation branch, run the pipeline, or write code. |
| **Work on an issue's documents:** "Let's explore #42 in its work folder." | Read the issue and existing documents. Save requested notes or drafts in `devdocs/work/42-<slug>/`. | Local drafts remain uncommitted by default. Do not automatically rewrite the GitHub issue or implement anything. |
| **Plan only:** "Prepare a plan for #42, but don't implement it." | Prepare a draft plan for review, distinguishing assumptions, decisions, and unresolved questions. If formal pipeline planning is explicitly requested, use the issue branch and applicable preparation steps. | Stop at the requested planning boundary. Draft/review-only work does not authorize commits or publication; neither kind of planning authorizes implementation. |
| **Implement an issue:** "Implement #42." | Use the linked issue branch and the required preparation, planning, critique, implementation, and verification process. Commit completed documents and code at the prescribed checkpoints, unless explicitly told not to commit. | Respect blockers and explicit limits. Implementation alone does not authorize merging or deployment. |
| **Commit a checkpoint:** "Commit these notes, although they're still a draft." | Commit only the specified documents on an allowed branch, clearly preserving their draft status. | A commit does not approve the proposal, complete a pipeline step, or authorize pushing. |
| **Publish an update:** "Post this revised understanding on #42." | Post the requested update. Preserve the original request, explain meaningful changes in understanding, and update status only where justified. | Do not publish unrelated local drafts or change implementation status without evidence. |
| **Pause and resume:** "Leave this here; we'll continue later." | Stop. If requested, save a handoff with decisions, open questions, and the next step. On resumption, read that context and any intervening changes first. | Do not keep working, publish a handoff automatically, or mark unfinished steps complete. |

A discussion or diagnosis may lead to a recommendation to open an issue; the
recommendation is not authorization to open it. Likewise, having an existing
issue does not prevent returning to discussion. A valid request is:

> "Explore alternatives for #42 in its work folder; don't implement, commit,
> or post to GitHub yet."

Read-only investigation still follows the full-file reading and evidence
standards in §11. It does not automatically authorize writing archaeology
refreshes or other files. Formal pipeline work still requires the session
warming in §4.1; discussion and cheap issue capture do not automatically start
that pipeline.

### 12.2 Where thinking and task documents live

**Before there is an issue:** use `devdocs/inquiries/<date-and-topic>/` for
requested local notes. An inquiry may produce zero, one, or several issues.
It is a place to think, not a second numbered task backlog. Do not invent a
scope number or a placeholder GitHub issue number to save an idea.

**Once there is an issue:** its task-specific working documents belong in
`devdocs/work/<issue-number>-<slug>/`. Reuse the folder and slug if they already
exist. Otherwise choose the slug using §6.2. Creating an issue alone does not
require creating a folder; create it when local documents are needed.

When promoting an inquiry into task work, carry the relevant task-specific
notes into the issue's folder and record their origin. Shared research may
remain in the inquiry folder and be linked from multiple issues. Do not move
shared research out from under another task or maintain two competing task
descriptions as separate backlogs.

**Local-only drafts may precede branch creation.** They can remain uncommitted
in the issue's work folder during discussion. A folder is not proof that a
branch exists or a pipeline step is complete. Before formal pipeline work,
create or use the linked issue branch under §6.2 and carry the relevant drafts
onto it without disturbing unrelated changes. This permission to keep local
drafts is not permission to commit them to `main` or to write application code
without the required issue and branch.

### 12.3 Drafts, completed documents, and commits

**Local drafts may remain uncommitted during discussion and revision. During
formal implementation work, commit each completed pipeline document before
advancing to the next step. A committed draft is still a draft.**

Mark exploratory documents as drafts and retain their open questions. Use
notes or a clearly named draft when exploring alternatives to an existing
description or plan; do not silently overwrite a completed document or remove
its recorded decisions. Revising an established plan follows the applicable
revision and critique rules in §§4 and 7.

Formal pipeline planning, when explicitly requested, uses the same completion
and commit checkpoints but stops at the requested planning stage. A request
for a draft plan does not claim those formal checkpoints have been completed.

If the user says "don't commit", respect it. Continue only the authorized
discussion or draft work, leave commit-dependent boxes unchecked, and explain
the pending checkpoint. Do not claim a formal step is complete or advance past
its required commit gate. Resuming formal execution requires resolving that
boundary with the user; it is not an excuse to commit against the instruction.

### 12.4 GitHub and local documents do not silently synchronize

GitHub owns the task's current status and discussion. Working files hold its
detailed reasoning, plans, critiques, and implementation reports. Preserve the
original issue request as required by §6.1.1; meaningful changes in
understanding should be deliberately summarized or linked, not blindly copied
over the original text.

Editing a local draft does not automatically authorize editing the issue,
posting a comment, or pushing a branch. When formal pipeline work is
authorized, perform the issue and PR updates that the applicable pipeline
steps require, subject to any explicit "don't publish" limit. If such a limit
blocks a required step, report the boundary rather than silently skipping it
or publishing anyway.

Be accurate about availability: distinguish a local, uncommitted document from
a committed and pushed one. Do not present a GitHub file link as usable before
that file exists at the linked revision, and do not mark work complete merely
because a file or folder exists.

### 12.5 GitHub issue titles describe the task, not its local references

**Use plain, descriptive issue titles that name the problem or requested
outcome.** When creating an issue, including an import from local documents,
do not add local tracking IDs, folder names, paths, or migration prefixes to
its title. This includes labels such as `[Scoped 139]`, `[Work 37]`,
`scoped/139`, or `devdocs/work/37-<slug>` used as title prefixes or suffixes.
GitHub assigns the issue number; do not repeat it in the title.

Local references belong in the issue body, its Docs field, or a migration
index when useful for traceability. They are metadata, not the task's name.

- Use: `Make the bot welcome useful to people looking for a home`.
- Do not use: `[Scoped 139] Make the bot welcome useful to people looking for a home`.
- Do not use: `[Work 37] Make the bot welcome useful to people looking for a home`.

This does not ban words such as "work" when they genuinely describe the task;
it bans adding local bookkeeping references to an otherwise descriptive title.

### 12.6 Read issue titles before creating or starting work

**Keep a lightweight picture of the repository's existing issues in the
session context. Read titles first, then read details only where relevant.**
This prevents duplicate tasks and makes related work, prerequisites, and
already-made decisions visible without loading every issue description.

**When to do it:**

- Before drafting or publishing a new issue, including an issue discovered
  during another task.
- Before formal planning or implementation of an existing issue, so adjacent
  work and dependencies are considered before a branch or plan is started.
- Not automatically on every read of this guide or every discussion-only
  turn. A recent, complete title list already in the session can be reused
  during the same discussion. Refresh it immediately before creating an issue
  and when starting or resuming formal work after a break or context loss.
  After creating or renaming an issue, update the session's title list.

**First pass — all titles, no descriptions.** Use `gh` against the intended
repository and read every page of both open and closed issues. Include only
the issue number, state, and title: the number identifies the issue, and the
state distinguishes pending work from history. Do not bulk-load bodies,
comments, or working documents. Do not treat `gh issue list`'s default result
limit as the complete backlog.

From the intended repository's checkout, this read-only query automatically
paginates and requests only those issue fields:

```bash
gh api graphql --paginate \
  -F owner='{owner}' -F name='{repo}' \
  -f query='
    query($owner: String!, $name: String!, $endCursor: String) {
      repository(owner: $owner, name: $name) {
        issues(first: 100, after: $endCursor, states: [OPEN, CLOSED]) {
          nodes { number title state }
          pageInfo { hasNextPage endCursor }
        }
      }
    }' \
  --jq '.data.repository.issues.nodes[] | "#\(.number) [\(.state)] \(.title)"'
```

Confirm the target repository before running it. Keep the compact output in
the working context; this check does not require creating another index file
or pasting the entire list into the user-facing answer. If tool output is
truncated, retrieve the remaining title rows in bounded batches rather than
claiming the truncated list was complete.

**Second pass — inspect plausible matches, not everything.** Compare the
request's intent with the titles, including different wording for the same
problem. Select likely duplicates, highly relevant adjacent tasks, and
possible prerequisites. Then read those issues' bodies, current status, and
relevant comments with `gh issue view <number> --comments`; follow linked
documents or explicit dependencies only as needed. Always read the selected
task itself before working on it. A title suggests a relationship; it does
not establish one.

Decide what the relationship actually is:

| Finding after reading the relevant issue | What to do |
|---|---|
| **The same task already exists** | Point to the existing issue and use it as the task reference instead of creating a duplicate. Do not silently expand its scope; posting new information still follows the request's publication limits. |
| **A related issue is closed** | Read its outcome before deciding whether the request is already satisfied, a regression, or a genuinely new follow-up. Do not reopen it automatically or assume closed means successfully shipped. |
| **An unfinished prerequisite exists** | Name the prerequisite, explain the dependency, and apply §4.5's blocked-work rules. Do not silently switch to implementing that other issue or build past the blocker. |
| **The work is related but independent** | Reference the relationship in the proposed or authorized issue update, while keeping the tasks distinct. Related does not automatically mean blocked. |
| **No existing issue covers the task** | Create a new issue only when creation is authorized, using §12.5's descriptive title rule and recording any verified relationships. |

Before publication or formal implementation, briefly report the relevant
matches and the resulting choice: reuse, distinct follow-up, prerequisite,
or new task. Checking titles is read-only permission, not permission to
create, edit, reopen, close, or implement additional issues.

If GitHub cannot be read, a page fails, or the title list is incomplete, say
so. Do not assert that no matching issue exists or bypass this check when
publishing a new issue or starting formal work. Unaffected local discussion
and drafting can continue with the limitation stated.
<!-- END EXPERIMENTAL WORKFLOW SCENARIOS -->

---

## Appendix 1 — The process guard hook

This is the script half of the hook §0.2 describes. Copy it to
`.claude/hooks/process-guard.sh`, make it executable (`chmod +x`), and commit it
together with the settings file shown in §0.2. **If a checkout has no
`.claude/hooks/process-guard.sh`, the hook is not installed, and it must be
installed before any other work.** Then restart the session, or open `/hooks`
once, so Claude Code loads it (§0.2, Install).

```bash
#!/usr/bin/env bash
# .claude/hooks/process-guard.sh
#
# Enforces CONTRIBUTING.md at the moment of the act, rather than trusting that
# whoever is working here read it. Wired as a PreToolUse hook on Bash.
#
# Three jobs, in order of severity:
#   1. BLOCK  `git commit` on dev or main            (CONTRIBUTING §8)
#   2. BLOCK  `gh pr create` with no merge-check.md  (CONTRIBUTING §7)
#   3. REMIND on `gh issue create` / `gh issue develop`
#
# Deliberately narrow: anything it does not recognise passes through untouched.
# A hook that blocks legitimate work is worse than no hook.
set -uo pipefail

payload="$(cat)"
cmd="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty' 2>/dev/null)"
[ -z "$cmd" ] && exit 0

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
branch="$(git -C "$repo_root" rev-parse --abbrev-ref HEAD 2>/dev/null)" || exit 0

# Scan the COMMAND CHAIN only, never a heredoc body. A commit message or a
# document that merely MENTIONS `gh pr create` must not trip the guard — it did,
# on this hook's own first commit. Truncating at the first `<<` keeps the real
# command (everything before the redirect) and drops the data after it. A `<<`
# inside a quoted string truncates early, which only makes the guard more
# permissive, never less.
scan="${cmd%%<<*}"

deny() {
  jq -nc --arg r "$1" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'
  exit 0
}
note() {
  jq -nc --arg c "$1" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",additionalContext:$c}}'
  exit 0
}
has() { printf '%s' "$scan" | grep -qE "$1"; }

# Every path this commit would touch. Staged files always; tracked-but-unstaged
# too when -a/--all is present, since those get swept in. `git commit <path>`
# leaves both empty, which reports "not docs-only" and therefore denies — the
# safe direction: over-denying a doc commit is a nuisance, over-allowing a src
# commit is the whole of §8 gone.
changed_paths() {
  { git -C "$repo_root" diff --cached --name-only 2>/dev/null
    if printf '%s' "$scan" | grep -qE '(^| )(-[a-zA-Z]*a[a-zA-Z]*|--all)( |$)'; then
      git -C "$repo_root" diff --name-only 2>/dev/null
    fi
  } | grep -v '^[[:space:]]*$' | sort -u
}

# Documentation-only: anything under devdocs/, or a top-level *.md, nothing
# else. Deliberately NOT .claude/ — a commit that edits the guard is a
# behaviour change and goes through a PR like any other.
#
# The `.+` after devdocs/ is load-bearing: `$` binds to the whole alternation,
# so `^(devdocs/|…)$` matched only a path that IS literally "devdocs/" and
# rejected every file under it. That shipped, and stayed invisible because the
# only commits using the carve-out were CONTRIBUTING.md, which matches the
# other branch.
docs_only() {
  local files
  files="$(changed_paths)"
  [ -z "$files" ] && return 1
  ! printf '%s\n' "$files" | grep -qvE '^(devdocs/.+|[^/]+\.md)$'
}

# ── 1. no direct commits to the trunk (§8) ──────────────────────────────
if has '(^|[;&|] *)git +(-[^ ]+ +)*commit([ ]|$)' \
   && ! printf '%s' "$scan" | grep -q -e '--dry-run'; then
  case "$branch" in
    dev|main)
      [ "${ALLOW_TRUNK_COMMIT:-}" = "1" ] && exit 0
      # A merge in progress is how work legitimately REACHES dev — §7.6's
      # doc-excluding recipe is `git merge --no-commit` then `git commit`.
      # Blocking that would block the only sanctioned way to integrate.
      git_dir="$(git -C "$repo_root" rev-parse --git-dir 2>/dev/null)"
      [ -n "$git_dir" ] && [ -f "$repo_root/$git_dir/MERGE_HEAD" ] && exit 0
      [ -n "$git_dir" ] && [ -f "$git_dir/MERGE_HEAD" ] && exit 0
      # Documentation-only commits land on dev directly (§8): no code diff for
      # the merge gate to check, and no plan to check it against. `main` is
      # excluded — it describes what users run, so even docs arrive by PR.
      [ "$branch" = "dev" ] && docs_only && exit 0
      deny "CONTRIBUTING.md §8 — no direct commits to '$branch'.

Work reaches dev by merged PR only, so the merge gate always has a diff to check against a plan. A direct commit has none, which is why it is refused rather than discouraged.

Do this instead:
  gh issue create --label bug|enhancement --title '...'
  gh issue develop <n> --base dev --name fix|feat/<n>-<slug> --checkout

Documentation-only commits (devdocs/ or a top-level *.md, nothing else) are allowed on dev — this commit touches code as well.

Genuine production emergency (§3.2): re-run with ALLOW_TRUNK_COMMIT=1, then open the issue retroactively the same day and write up what was done."
      ;;
  esac
fi

# ── 2. the merge gate must have run (§7) ────────────────────────────────
if has 'gh +pr +create([ ]|$)'; then
  if printf '%s' "$branch" | grep -qE '^(fix|feat)/[0-9]+-'; then
    issue="$(printf '%s' "$branch" | sed -E 's#^(fix|feat)/([0-9]+)-.*#\2#')"
    if ! ls "$repo_root"/devdocs/work/"$issue"-*/merge-check.md >/dev/null 2>&1; then
      deny "CONTRIBUTING.md §7 — the merge gate has not run for issue #${issue}.

No devdocs/work/${issue}-*/merge-check.md exists on this branch.

Read desc.md, plan.md (revision 2), critic.md and the actual diff TOGETHER, then answer the gate's questions in merge-check.md and commit it:
  0. Was the work done warm, and was it weighed?
  0b. Did the diff stay inside what triage surfaced?
  1. Does the implementation match the plan?
  2. Does the plan still make sense against what the code turned out to be?
  3. Were the critic's High and Medium findings answered?
  4. Is the issue's status block complete and honest?"
    fi
  fi
fi

# ── 3. reminders at the process moments ─────────────────────────────────
if has 'gh +issue +create([ ]|$)'; then
  note "CONTRIBUTING §6.1 — label it 'bug' or 'enhancement'; that choice decides the branch and the path, so do not guess it on someone's behalf. The body is the request in the requester's own words: a one-line issue is a good issue. desc.md is the spec and comes later, on the branch, after warming and triage. Append the §6.5 pipeline status block to the body."
fi

if has 'gh +issue +develop([ ]|$)'; then
  note "CONTRIBUTING §4.1 and §4.3 — on the new branch: warm first UNLESS this session is already warm (context survives git checkout; warming is per session, not per branch). Then triage: /surfacing to see what the work touches, weigh it light or heavy, commit triage.md and label the issue. Do not plan from the issue title — triage routinely changes what an issue is about."
fi

exit 0
```

---

## Appendix 2 — Releases: what reaches production, and how

**Production runs only what is on `main`.** Whatever updates production takes
its code from `main`, never from `dev`, a work branch or someone's checkout.
Updating production is always a deliberate act, done when a batch is declared
ready.

**`dev` may feed a staging host.** A staging release can take its code from
`dev`, automatically on every merge or by hand. Staging is where a batch is
tried before it becomes a release.

**Nothing on `dev` or a work branch may update production.** Not
automatically, not as a side effect of a build, and not through a hosting
setting that treats every branch alike. Work branches deploy nowhere, or only
to private previews users cannot reach.

**Any of these ways of releasing fits the convention:**

- **A release tag on `main`.** Publishing a tagged release on `main` triggers
  the production deploy, for example through CI. Pushes to `dev` deploy to
  staging or to nothing.
- **A release command.** A script deploys a named target: staging from `dev`,
  production only from a release tag on `main`. It refuses every other
  combination.
- **Deploy on merge to `main`.** The hosting publishes whenever `main`
  changes. Since `main` changes only through a pull request from `dev`, that
  merge is the release. Every other branch must be set not to deploy.
- **A mix.** Different parts of the product may release differently, such as
  a website that publishes on merge to `main` and a server that deploys on a
  tag. Each part follows the rules above.

**Rolling back** returns production to an earlier release from `main`, by the
same mechanism or the hosting's own rollback. It never means deploying a
branch.

**Check it once when adopting this process.** Push a throwaway branch whose
files match production, and confirm nothing was deployed. A single hosting
setting can make every branch publish, and nobody notices until a branch goes
live.

**The project card records the choice:** which of these each part of the
product uses, what triggers a staging release and a production release, and
how to see which release production is running.

---

## Appendix 3 — Working without `/surfacing` or `/traverse`

**`/surfacing` and `/traverse` are private skills.** They are not in the
AlignCraft pack (§0.3), so most sessions will not have them. Their absence
never skips a step: the session does the same work by hand, with
**`ultrathink`** in the prompt so the model spends real reasoning on it instead
of answering from the request's own words.

### Without `/surfacing` — re-read everything relevant

Surfacing answers *"what does this work actually touch?"* (§4.3). Without the
skill, answer it by reading:

1. **Re-read, in full, everything the request could reach** — the code it
   names, the code that calls it and that it calls, their tests, and the
   documents that describe them. Whole files, not search hits (§10.2).
2. **Follow each one outward** until another step brings in nothing new.
3. **Write `triage.md` from what you read** — what the work touches, the
   weight, why, and what to watch for (§4.3). Anything you did not read in
   full does not go on the list.

### Without `/traverse` — find the meaning gaps, then stabilize the most vital one

Traverse answers *"what does this request actually mean here?"* (§5). Without
the skill:

1. **Extract the meaning gaps** — every place where the request's words could
   mean more than one thing, or where they meet something the repository
   already holds that could change what they mean.
2. **Take the most vital gap first** — the one whose answer would most change
   what gets built.
3. **Stabilize its meaning.** Read what the repository holds that bears on it,
   test each reading against that, and settle on the reading that holds. When
   only the requester can settle it, write the question down for them instead
   of guessing.
4. **Leave the understanding firmer than you found it.** If another gap would
   still change what gets built, take it next, the same way.

Write the result to the meaning-gaps folder,
`devdocs/meaning_gaps/<issue>-<slug>.md`: the gaps found, the order you took
them in, the reading each one settled on or the question still open, and the
readings that died. It is the raw material for `desc.md`, as `traverse/` would
have been.
