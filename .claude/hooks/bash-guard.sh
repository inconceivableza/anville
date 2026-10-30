#!/usr/bin/env bash
# ✨ PreToolUse guard for Bash: refuses or asks about the git shapes the developer's working rules cover, naming the rule,
# redirects deletes to trash, and refuses any command that arrives without a description of what it does.
# Reads the hook's JSON on stdin; prints a deny or ask decision, or nothing to let the command run.

input=$(cat)
command=$(jq -r '.tool_input.command // empty' <<<"$input")
description=$(jq -r '.tool_input.description // empty' <<<"$input")
git='git( -C [^ ]+)?'

decide() {
  jq -n --arg decision "$1" --arg reason "$2" \
    '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: $decision, permissionDecisionReason: $reason}}'
  exit 0
}

if [ "$(wc -w <<<"$description")" -lt 3 ]; then
  decide deny "Say what this command does in a few plain words (description field) before running it."
fi
if grep -Eq "$git push( |$)" <<<"$command"; then
  decide deny "Never push: flag the push point and let the developer push."
fi
if grep -Eq "$git add( [^|;&]*)? (-A|--all|\.)( |$)" <<<"$command"; then
  decide ask "Stages everything rather than files by name (git workflow memory)."
fi
if grep -Eq "$git commit[^|;&]*--no-edit" <<<"$command"; then
  decide ask "Uses --no-edit rather than the plain form (git workflow memory)."
fi
if grep -Eq "$git (commit|merge|push)[^|;&]*(--no-verify|-n( |\$))" <<<"$command"; then
  decide ask "Skips the pre-commit checks; fix what they refuse instead (only the developer skips them)."
fi

# Deletes go to the Bin so an approved one can still be undone; git rm is left alone since git can recover it.
# Quoted text is taken out first, so a search for "rm " (a grep pattern) is not taken for a delete (06, run 1),
# unless something will run that text as a command (sh -c, bash -c, eval), when it is checked as it stands.
unquoted="$command"
if ! grep -Eq '(^|[^[:alnum:]_])(sh|bash|zsh) +-c|(^|[^[:alnum:]_])eval( |$)' <<<"$command"; then
  unquoted=$(sed -E "s/'[^']*'//g; s/\"[^\"]*\"//g" <<<"$command")
fi
if grep -Eq "(^|[;&|(\"']|xargs|sudo|-exec)[[:space:]]*rm( |\$)" <<<"$unquoted"; then
  decide deny "Use trash instead of rm, so the delete lands in the Bin and can be put back (trash-not-rm memory)."
fi
if grep -Eq '(^|[[:space:]])find( [^|;&]*)? -delete( |$)' <<<"$unquoted"; then
  decide deny "Use find … -exec trash {} + instead of -delete, so the delete lands in the Bin (trash-not-rm memory)."
fi
if grep -Eq "$git clean( |$)" <<<"$command"; then
  decide ask "git clean deletes untracked files outright; list them with git clean -n and trash them instead (trash-not-rm memory)."
fi

# Inside a build's ticket or integration worktree the developer reviews the diff, not each edit, so shell writes there
# are left to run (developer's call, 27 Oct). A command that names a worktree is taken to work in it.
if grep -q '/\.claude/worktrees/' <<<"$command"; then
  exit 0
fi

# Shell writes hide the change that Edit/Write would show. Harmless redirects (2>&1, >/dev/null) are stripped first.
# Quoted text is left out here too, so a ">" or "<<" inside a search pattern is not taken for a write.
writes=$(sed -E 's/[0-9]*>&[0-9-]//g; s/[0-9]*>[[:space:]]*\/dev\/null//g' <<<"$unquoted")
if grep -Eq '(^|[^[:alnum:]_-])sed( [^|;&]*)? (-[a-zA-Z]*i|--in-place)' <<<"$unquoted" \
  || grep -Eq '(^|[^-=])>' <<<"$writes" \
  || grep -Eq '(^|[^<])<<[^<]' <<<"$unquoted" \
  || grep -Eq '(^|[|[:space:]])tee( |$)' <<<"$unquoted"; then
  decide ask "Writes a file from the shell; Edit/Write would show the change (dedicated-file-tools memory)."
fi
