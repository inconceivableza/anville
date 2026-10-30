#!/usr/bin/env bash
# ✨ PreToolUse reminder for Read and Bash: when the call names a skill's SKILL.md whose frontmatter has
# disable-model-invocation: true, adds context saying the skill is the developer's to type, not ours to carry out.
# Never blocks. Matches .claude/skills/ and .agents/skills/ (the first links to the second).

input=$(cat)
paths=$(jq -r '.tool_input.file_path // empty, .tool_input.command // empty' <<<"$input" \
  | grep -Eo "[^ '\"]*(\.claude|\.agents)/skills/[^/ '\"]+/SKILL\.md")
[ -z "$paths" ] && exit 0

project=${CLAUDE_PROJECT_DIR:-$(jq -r '.cwd // empty' <<<"$input")}
names=()
while IFS= read -r path; do
  case $path in /*) file=$path ;; *) file=$project/$path ;; esac
  [ -f "$file" ] || continue
  # Frontmatter only: the lines between the first two --- markers.
  if awk '/^---[[:space:]]*$/ { n++; next } n == 1' "$file" | grep -Eq '^disable-model-invocation:[[:space:]]*true'; then
    names+=("$(basename "$(dirname "$path")")")
  fi
done <<<"$paths"
[ ${#names[@]} -eq 0 ] && exit 0

list=$(printf '/%s, ' "${names[@]}")
jq -n --arg context "User-only skill (${list%, }): describe or compare it, never carry out its steps; tell the developer to type it." \
  '{hookSpecificOutput: {hookEventName: "PreToolUse", additionalContext: $context}}'
