#!/usr/bin/env bash
set -euo pipefail

prompt_text="${1:-请选择本次原型输出目录}"
default_dir="${2:-$HOME/Documents}"

if [[ "$(uname -s)" != "Darwin" ]]; then
  printf '%s\n' "choose_output_folder.sh only supports macOS." >&2
  exit 2
fi

if ! command -v osascript >/dev/null 2>&1; then
  printf '%s\n' "choose_output_folder.sh requires osascript." >&2
  exit 3
fi

if [[ ! -d "$default_dir" ]]; then
  default_dir="$HOME"
fi

if [[ ! -d "$default_dir" ]]; then
  default_dir="/"
fi

tmp_err="$(mktemp)"
trap 'rm -f "$tmp_err"' EXIT

if ! selected_path="$(
  osascript - "$prompt_text" "$default_dir" 2>"$tmp_err" <<'APPLESCRIPT'
on run argv
  set promptText to item 1 of argv
  set defaultDirPOSIX to item 2 of argv
  set chosenFolder to choose folder with prompt promptText default location (POSIX file defaultDirPOSIX)
  return POSIX path of chosenFolder
end run
APPLESCRIPT
)"; then
  error_text="$(cat "$tmp_err")"
  if [[ "$error_text" == *"(-128)"* ]]; then
    printf '%s\n' "Folder selection canceled by user." >&2
    exit 130
  fi

  printf '%s\n' "Failed to open macOS folder picker." >&2
  if [[ -n "$error_text" ]]; then
    printf '%s\n' "$error_text" >&2
  fi
  exit 1
fi

printf '%s\n' "$selected_path"
