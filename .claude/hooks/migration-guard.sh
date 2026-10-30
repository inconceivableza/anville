#!/usr/bin/env bash
# ✨ PreToolUse guard for Write, Edit and MultiEdit: a Django migration (a numbered file under migrations/) is generated
# with makemigrations, never written or edited by hand, so such a call asks the developer first, with the reason.
# Asks rather than denies, as the rest of the project's guards do; any other file passes untouched.

input=$(cat)
path=$(jq -r '.tool_input.file_path // empty' <<<"$input")
[[ $path =~ (^|/)migrations/[0-9][^/]*\.py$ ]] || exit 0

jq -n --arg reason "$(basename "$path") is a migration: migrations are generated with makemigrations, not written or edited by hand." \
  '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "ask", permissionDecisionReason: $reason}}'
