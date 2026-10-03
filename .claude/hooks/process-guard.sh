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
