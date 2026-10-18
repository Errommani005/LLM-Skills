#!/usr/bin/env bash
# Gate G1: the project boots headless with zero script errors.
# usage: gate_boot.sh <project-root>        (set GODOT=/path/to/godot if it is not on PATH)
set -u
GODOT="${GODOT:-godot}"
ROOT="${1:-.}"
command -v "$GODOT" >/dev/null || { echo "godot not found: set GODOT=/path/to/godot"; exit 2; }
"$GODOT" --headless --path "$ROOT" --import >/dev/null 2>&1          # build the import cache first
OUT=$("$GODOT" --headless --path "$ROOT" --quit-after 120 2>&1)
if echo "$OUT" | grep -qE "SCRIPT ERROR|Parse Error|ERROR:|Failed to load"; then
  echo "G1 FAIL"; echo "$OUT" | grep -E "SCRIPT ERROR|Parse Error|ERROR:|Failed to load|at:" | head -20; exit 1
fi
echo "G1 PASS (booted, no script errors)"
