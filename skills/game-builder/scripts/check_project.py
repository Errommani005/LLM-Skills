#!/usr/bin/env python3
"""Check a project against the game-builder standard. Exit 1 if any ERROR.

usage: check_project.py <project-root> [--engine godot|unity|unreal]
Engine is auto-detected: project.godot = Godot; ProjectSettings/ProjectVersion.txt or Packages/manifest.json = Unity; *.uproject = Unreal.
ERROR = breaks a hard rule.  WARN = look at it, justify it with a comment, or fix it.
"""
import pathlib, re, sys

MAX_FILE, MAX_FUNC, MAX_AUTOLOADS = 300, 20, 3
DOCS = ["GAME_VISION.md", "STYLE_BIBLE.md", "DECISIONS.md", "CREDITS.md", "TOOLCHAIN.md"]
ASSET_EXT = {".glb", ".gltf", ".fbx", ".ogg", ".wav", ".mp3", ".png", ".jpg", ".svg", ".tga", ".exr", ".uasset"}
SKIP = {".godot", "addons", ".git", "evidence", ".claude", "Library", "Temp", "Packages", "Intermediate", "Saved", "Binaries",
        "DerivedDataCache", "obj", "Logs", "UserSettings", "ThirdParty", "Plugins", "node_modules", "TextMesh Pro", "Samples"}
args = [x for x in sys.argv[1:] if not x.startswith("--")]
root = pathlib.Path(args[0] if args else ".").resolve()
engine = None
if "--engine" in sys.argv:
    engine = sys.argv[sys.argv.index("--engine") + 1]
if not engine:
    if (root / "project.godot").exists(): engine = "godot"
    elif (root / "ProjectSettings" / "ProjectVersion.txt").exists() or (root / "Packages" / "manifest.json").exists(): engine = "unity"
    elif list(root.glob("*.uproject")): engine = "unreal"
    else: engine = "godot"
SRC = {"godot": (".gd",), "unity": (".cs",), "unreal": (".h", ".cpp")}[engine]
COMMENT = "#" if engine == "godot" else "//"
errors, warns = [], []
def err(m): errors.append(m)
def warn(m): warns.append(m)

def files(exts):
    out = []
    for e in exts:
        out += [p for p in root.rglob(f"*{e}") if not (set(p.relative_to(root).parts) & SKIP)]
    return out

# 1. required docs
for d in DOCS:
    p = root / "_project" / d
    if not p.exists(): err(f"missing _project/{d}")
    elif "<<FILL" in p.read_text(): warn(f"_project/{d} still has <<FILL>> placeholders")
for d in ["ARCHITECTURE.md", "README.md"]:
    if not (root / d).exists(): err(f"missing {d}")

# 2. engine-specific hard rules
if engine == "godot":
    pg = root / "project.godot"
    if not pg.exists(): err("no project.godot")
    else:
        m = re.search(r"\[autoload\](.*?)(\n\[|\Z)", pg.read_text(), re.S)
        n = len([l for l in (m.group(1).splitlines() if m else []) if "=" in l])
        if n > MAX_AUTOLOADS: err(f"{n} autoloads (max {MAX_AUTOLOADS}: Events, State, Net)")

# 3. scripts: header, size, function length (GDScript only)
sources = files(SRC)
for p in sources:
    rel = p.relative_to(root)
    lines = p.read_text(errors="ignore").splitlines()
    first = next((l for l in lines if l.strip()), "")
    is_test = "tests" in [x.lower() for x in rel.parts]
    if not (first.startswith(COMMENT) or first.startswith("/*")):
        err(f"{rel}: no header comment (WHAT / TALKS TO / SIBLINGS)")
    elif not any("WHAT" in l for l in lines[:8]) and not is_test:
        warn(f"{rel}: header lacks a WHAT: line")
    if len(lines) > MAX_FILE and not any("WHY LONG" in l for l in lines[:10]):
        warn(f"{rel}: {len(lines)} lines (cap ~{MAX_FILE}); split by category or add a 'WHY LONG:' header line")
    if engine == "godot" and not is_test:
        start = None
        for i, l in enumerate(lines + ["end"]):
            top = l and not l[0].isspace() and not l.startswith("#")
            if top and start is not None:
                body = [x for x in lines[start[1]:i] if x.strip() and not x.strip().startswith("#")]
                if len(body) > MAX_FUNC + 1: warn(f"{rel}: func {start[0]}() is {len(body)-1} lines (cap ~{MAX_FUNC})")
                start = None
            if l.startswith("func ") or l.startswith("static func "):
                start = (re.sub(r"^(static )?func (\w+).*", r"\2", l), i)

# 4. folders documented
arch = (root / "ARCHITECTURE.md").read_text() if (root / "ARCHITECTURE.md").exists() else ""
scan = {"godot": root, "unity": root / "Assets" / "Game", "unreal": root / "Content"}[engine]
if scan.exists():
    for d in sorted(p for p in scan.iterdir() if p.is_dir() and p.name not in SKIP and not p.name.startswith(".") and p.name != "_project"):
        if f"{d.name}/" not in arch: warn(f"folder {d.relative_to(root)}/ is not described in ARCHITECTURE.md")
elif engine != "godot":
    warn(f"expected folder {scan.relative_to(root)}/ not found")

# 5. credits coverage
base = {"godot": root, "unity": root / "Assets" / "Game", "unreal": root / "Content"}[engine]
assets = [p for e in ASSET_EXT for p in base.rglob(f"*{e}")
          if base.exists() and not (set(p.relative_to(root).parts) & SKIP) and p.relative_to(root).parts[0] not in ("_project", "shared")] if base.exists() else []
credits = root / "_project" / "CREDITS.md"
rows = len([l for l in credits.read_text().splitlines() if l.startswith("|")]) - 2 if credits.exists() else 0
if assets and rows < 1: warn(f"{len(assets)} asset files but CREDITS.md has no rows (log source + license for each)")

print(f"Checked {root} [{engine}]: {len(sources)} scripts, {len(assets)} assets")
for e in errors: print("ERROR:", e)
for w in warns:  print("WARN: ", w)
if not errors and not warns: print("All good.")
sys.exit(1 if errors else 0)
