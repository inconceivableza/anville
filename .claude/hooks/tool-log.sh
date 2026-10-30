#!/usr/bin/env bash
# ✨ PostToolUse audit log: appends one line per tool call to .claude/tool-log.txt so the developer can follow it with
# `bin/tool-log` (or `tail -f`). Logs who made the call, the stated description and the target (command, path, URL
# or query, shortened); never file contents. Bash commands keep up to 1000 characters so bin/build-watch can see a
# commit behind a long git add; the viewers trim them back for display. A new file starts each day; earlier days are kept as tool-log.<date>.txt.

log="$CLAUDE_PROJECT_DIR/.claude/tool-log.txt"
today=$(date +%Y-%m-%d)
if [ -f "$log" ]; then
  logged=$(stat -f %Sm -t %Y-%m-%d "$log")
  [ "$logged" != "$today" ] && mv "$log" "$CLAUDE_PROJECT_DIR/.claude/tool-log.$logged.txt"
fi

jq -r --arg root "$CLAUDE_PROJECT_DIR" '
  def pad($n): if length < $n then . + (" " * ($n - length)) else . end;
  def clip($n): if length > $n then .[0:$n - 1] + "…" else . end;
  # Worktrees as [B2], the project root dropped, the scratchpad as scratch/, newlines as ⏎.
  def short:
    gsub($root + "/\\.claude/worktrees/(?<w>[^/ ]+)/"; "[\(.w)] ")
    | gsub($root + "/\\.claude/worktrees/(?<w>[^/ ]+)"; "[\(.w)]")
    | gsub($root + "/"; "") | gsub($root; ".")
    | gsub("/private/tmp/claude-[^ ]*/scratchpad/"; "scratch/")
    | gsub("\n"; " ⏎ ");
  (.tool_input // {}) as $in
  | .tool_name as $tool
  # A subagent shows as ↳ and the start of its id, the same on every line it logs.
  | (if .agent_id then "↳" + .agent_id[0:5] else "main" end) as $who
  | (($in.command // $in.file_path // $in.url // $in.query // $in.pattern // $in.path // $in.to // "-")
      | tostring | short | clip(if $tool == "Bash" then 1000 else 140 end)) as $target
  | ($in.description // $in.summary // "" | tostring | gsub("\n"; " ")) as $why
  | (now | localtime | strftime("%H:%M:%S")) + "  " + ($who | pad(6)) + "  " + (.tool_name | pad(10)) + "  "
    + (if $why != "" then $why + "  ┊ " + $target else $target end)
' >>"$log"
