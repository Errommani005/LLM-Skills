#!/usr/bin/env python3
"""Validate a game build prompt before handing it to the user.

usage: check_prompt.py <prompt.md>
The prompt starts at the first line matching '# ... Build Prompt' (anything before it, such as an intro, is ignored).
ERROR = the prompt is broken or incomplete.  WARN = probably wrong, look at it.  Exit 1 if any ERROR.
"""
import pathlib, re, sys

if len(sys.argv) < 2:
    sys.exit(__doc__)
raw = pathlib.Path(sys.argv[1]).read_text()
lines = raw.splitlines()
start = next((i for i, l in enumerate(lines) if re.match(r"^# .*Build Prompt", l)), None)
if start is None:
    sys.exit("ERROR: no '# <Game>: Build Prompt' title line found")
lines = lines[start:]
text = "\n".join(lines)
low = text.lower()
errors, warns = [], []
def err(m): errors.append(m)
def warn(m): warns.append(m)

# 1. required structure
for part in ["PART 1", "PART 2", "PART 3", "PART 4"]:
    if part not in text:
        err(f"missing '{part}' heading")
required = {
    "1.1": "Pitch", "1.2": "Objective", "1.3": "mechanics", "1.5": "Interface", "1.6": "Fun",
    "2.1": "Engine", "2.2": "style", "2.3": "Assets", "2.5": "budget", "2.6": "Architecture", "2.7": "Code style",
    "2.8": "Execution", "2.9": "Definition", "3.1": "ASK", "3.2": "DEFAULT", "3.3": "builder",
}
headings = {}
for l in lines:
    m = re.match(r"^#{2,4}\s+(\d+\.\d+)\s+(.*)", l)
    if m:
        headings[m.group(1)] = m.group(2)
for num, word in required.items():
    if num not in headings:
        err(f"missing section {num} ({word})")
    elif word.lower() not in headings[num].lower():
        warn(f"section {num} is titled '{headings[num]}' (expected it to cover: {word})")

# 2. unresolved placeholders and filler
for pat, label in [(r"\{\{.*?\}\}", "{{placeholder}}"), (r"<<.*?>>", "<<placeholder>>"), (r"\bTODO\b", "TODO"),
                   (r"\bTBD\b", "TBD"), (r"\bXXX\b", "XXX"), (r"^>\s", "leftover template guidance line (starts with '> ')")]:
    hits = [i + 1 for i, l in enumerate(lines) if re.search(pat, l)]
    if hits:
        err(f"{label} left in the prompt at relative line(s) {hits[:6]}")

# 3. cross-references
for m in re.finditer(r"§\s*(\d+\.\d+)", text):
    if m.group(1) not in headings:
        err(f"reference §{m.group(1)} points at a section that does not exist")

# 4. tags
tags = set(re.findall(r"\[([A-Z]{3,})\]", text))
for t in sorted(tags - {"ASK", "DEFAULT"}):
    warn(f"unknown tag [{t}] (only [ASK] and [DEFAULT] are allowed)")
sec31 = re.search(r"### 3\.1.*?(?=\n### 3\.2)", text, re.S)
sec32 = re.search(r"### 3\.2.*?(?=\n### 3\.3)", text, re.S)
if sec31 and "[ASK]" not in sec31.group(0): warn("section 3.1 has no [ASK] items")
if sec32 and "[DEFAULT]" not in sec32.group(0): warn("section 3.2 has no [DEFAULT] items")

# 5. engine consistency
eng_line = re.search(r"^### 2\.1.*?\n(.*?)(?=\n###|\n---)", text, re.S | re.M)
eng_text = (eng_line.group(1) if eng_line else "").lower()
engine = "godot" if "godot" in eng_text else "unity" if "unity" in eng_text else "unreal" if "unreal" in eng_text else None
if engine is None:
    err("section 2.1 does not name the engine (Godot, Unity or Unreal)")
else:
    wrong = {"godot": [r"\.cs\b", r"monobehaviour", r"\bprefab", r"blueprint", r"\.uasset", r"\.umap"],
             "unity": [r"\.gd\b", r"gdscript", r"\.tscn", r"autoload", r"blueprint", r"\.umap"],
             "unreal": [r"\.gd\b", r"gdscript", r"\.tscn", r"autoload", r"monobehaviour", r"\.prefab"]}[engine]
    arch = re.search(r"### 2\.6.*?(?=\n### 2\.7)", text, re.S)
    scope = (arch.group(0) if arch else "").lower()
    for w in wrong:
        if re.search(w, scope):
            warn(f"section 2.6 mentions '{w}' but the engine is {engine}: wrong vocabulary?")

# 5b. engine named in Part 4 matches 2.1
p4 = re.search(r"## PART 4.*", text, re.S)
p4t = p4.group(0).lower() if p4 else ""
if engine and p4 and f"engine: {engine}" not in p4t:
    warn(f"Part 4 does not start its tool block with 'ENGINE: {engine.title()}...'")

# 6. budget, gates, tools, risks
if "$0" not in text: err("the $0 budget is never stated")
for g in ["G1", "G2", "G3", "G5"]:
    if g not in text: err(f"gate {g} is not defined in the execution rules")
networked = bool(re.search(r"multiplayer|room code|peer-to-peer|online", low))
if networked and "G4" not in text: err("the game is multiplayer but gate G4 is missing")
if "edge case" not in low: err("no edge-case instruction")
if "human" not in low or "architecture.md" not in low: warn("the human-reviewer / ARCHITECTURE.md requirement is missing")
if "decided by the builder" not in low: warn("section 3.3 'decided by the builder' is missing (the builder must own the rest)")
if p4 and not re.search(r"claude mcp add|package manager|npx skills add|/plugin marketplace|pip install", p4t):
    warn("Part 4 has no install command for any tool")
if p4 and "verify" not in p4t: warn("Part 4 has no 'verify' markers (free tiers and versions drift)")
if "voice" in low and not re.search(r"fallback|discord", low): warn("voice chat is required but no $0 fallback is given")
if re.search(r"matchmaking|ranked|dedicated server", low) and "$0" in text and "friends-only" not in low and "not " not in low:
    warn("matchmaking/dedicated servers mentioned without a $0 note")
if "bug-free" in low and "gate" not in low: warn("'bug-free' is promised without gates")

# 7. size sanity
n = len(lines)
if n < 60: warn(f"only {n} lines: probably missing content")
if n > 600: warn(f"{n} lines: probably over-specified (the builder decides the rest)")
nums = len(re.findall(r"\b\d+(?:\.\d+)?\s*(?:px|ms|fps|m/s|kg|units?)\b", low))
if nums > 25: warn(f"{nums} hard-coded unit values: are you specifying tuning the builder should decide?")

print(f"Checked build prompt ({n} lines, engine: {engine or 'unknown'}, {len(headings)} numbered sections, tags: {sorted(tags)})")
for e in errors: print("ERROR:", e)
for w in warns: print("WARN: ", w)
if not errors and not warns: print("All good.")
sys.exit(1 if errors else 0)
