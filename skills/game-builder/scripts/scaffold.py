#!/usr/bin/env python3
"""Create a project skeleton that follows the game-builder standard.

usage: scaffold.py --name "Haunted Mall" --type party-coop --net online --path ./haunted-mall
                   [--engine godot|unity|unreal] [--engine-version 4.7] [--no-agents]

types:  party-coop platformer shooter racing puzzle strategy survival narrative arcade
net:    none (single player) | local (same screen) | lan | online
engine: godot (default): creates a full booting project.
        unity / unreal: run INSIDE an existing project (create it first in Unity Hub / the Unreal launcher);
        adds _project docs, category folders, agents. No engine code stubs are generated for them.
"""
import argparse, pathlib, re, shutil, sys

SKILL = pathlib.Path(__file__).resolve().parent.parent
HERE = SKILL / "assets" / "templates"
AGENTS = SKILL / "assets" / "agents"

DESC = {
    "_project": "Design docs: vision, style bible, decisions, credits, toolchain, evidence screenshots.",
    "shared": "Palette, the one shared shader/material, and the shared seams (state, events).",
    "audio/music": "Music tracks.", "audio/sfx": "Sound effects.",
    "ui/main_menu": "Title screen.", "ui/hud": "In-game overlay (score, timer, prompts).",
    "ui/game_over": "Defeat screen.", "ui/victory": "Win screen.", "ui/settings": "Volume, controls, quality.",
    "ui/room": "Lobby: player list, room code, Start button.",
    "network": "All multiplayer code (host, join, room codes, kick).",
    "addons": "Pinned third-party code (e.g. GUT). Never edit by hand.",
    "tests": "Automated tests and the multiplayer smoke test.",
    "levels/level1": "The first level: scene, script, and the objects that live only here.",
    "levels/world1/level1": "First level of world 1.", "levels/arena1": "The first arena.",
    "tracks/track1": "First race track: scene, script, checkpoints.",
    "maps/map1": "First map: terrain, spawn points, resources.",
    "characters/players": "Player scene, script and models.", "characters/player": "Player scene, script and models.",
    "characters/enemies": "Enemy scenes, scripts and models.", "characters/npcs": "Non-player characters.",
    "objects": "Props shared by several levels (each: scene + script + models).",
    "objects/pickups": "Collectibles.", "objects/hazards": "Things that hurt.",
    "weapons": "Weapons and projectiles.", "vehicles": "Vehicles and vehicles script.",
    "units": "Unit types (data + scene).", "buildings": "Building types (data + scene).",
    "puzzles": "One data file per puzzle/level; rules live in board/.", "board": "Pure puzzle rules, no visuals.",
    "items": "Item definitions.", "crafting": "Recipes.", "world": "World generation and chunks.",
    "data": "Tables of numbers (costs, waves, recipes).",
    "story": "Dialogue and branching script data.", "scenes": "Story scenes (backgrounds + characters).",
    "saves": "Save-file code (not the save data itself).",
}
BASE = ["shared", "audio/music", "audio/sfx", "ui/main_menu", "ui/hud", "ui/game_over", "ui/victory", "ui/settings", "tests"]
TYPES = {
    "party-coop": ["levels/level1", "characters/players", "characters/enemies", "objects"],
    "platformer": ["levels/world1/level1", "characters/player", "characters/enemies", "objects/pickups", "objects/hazards"],
    "shooter":    ["levels/arena1", "characters/player", "characters/enemies", "weapons", "objects"],
    "racing":     ["tracks/track1", "vehicles", "objects"],
    "puzzle":     ["puzzles", "board", "objects"],
    "strategy":   ["maps/map1", "units", "buildings", "data"],
    "survival":   ["world", "characters/player", "characters/enemies", "items", "crafting", "data", "saves"],
    "narrative":  ["story", "scenes", "characters/npcs"],
    "arcade":     ["levels/level1", "characters/player", "characters/enemies", "objects"],
}
ENGINE_NAMES = {"godot": "Godot", "unity": "Unity", "unreal": "Unreal Engine"}
ENGINE_BLOCKS = {
    "godot": ('Engine:        Godot {V} stable (pinned; do not upgrade mid-project)\nLanguage:      GDScript\n'
              'Editor MCP:    claude mcp add godot -e GODOT_PATH=/path/to/godot -- npx @coding-solo/godot-mcp   (MIT)\n'
              'Tests:         GUT 9.x (addons/gut), headless; scripts/gate_boot.sh and scripts/net_test.sh'),
    "unity": ('Engine:        Unity {V} LTS (pinned)\nLanguage:      C#, URP\n'
              'Editor MCP:    Package Manager git URL https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#<pinned tag>   (or IvanMurzak/Unity-MCP)\n'
              'Networking:    <<FILL NGO | Mirror; free-tier limits of Relay/Vivox if used>>\n'
              'Tests:         Unity Test Framework (EditMode/PlayMode)'),
    "unreal": ('Engine:        Unreal Engine {V} (pinned)\nLanguage:      C++ base classes + Blueprint subclasses (confirm with user)\n'
               'Editor MCP:    ChiR24/Unreal_mcp (MIT) | Epic official Unreal MCP (5.8, experimental) | ATDev uemcp   <<FILL the one chosen>>\n'
               'Networking:    built-in replication, listen server; <<FILL EOS terms if used>>\n'
               'Tests:         Automation / Functional Tests'),
}

def pascal(path):
    return "/".join("UI" if seg == "ui" else "".join(w[:1].upper() + w[1:] for w in re.split(r"[_ ]", seg)) for seg in path.split("/"))

def fill(text, ctx):
    for k, v in ctx.items():
        text = text.replace("{{%s}}" % k, v)
    return text

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--type", required=True, choices=sorted(TYPES))
    ap.add_argument("--net", default="none", choices=["none", "local", "lan", "online"])
    ap.add_argument("--path", required=True)
    ap.add_argument("--engine", default="godot", choices=sorted(ENGINE_NAMES))
    ap.add_argument("--engine-version", default=None)
    ap.add_argument("--godot", default=None, help=argparse.SUPPRESS)   # old flag, kept for compatibility
    ap.add_argument("--no-agents", action="store_true")
    a = ap.parse_args()

    ev = a.engine_version or a.godot or {"godot": "4.7", "unity": "6.3", "unreal": "5.8"}[a.engine]
    root = pathlib.Path(a.path)
    networked = a.net in ("lan", "online")
    game = re.sub(r"[^A-Za-z0-9]", "", a.name) or "Game"

    if a.engine == "godot":
        if root.exists() and any(root.iterdir()):
            sys.exit(f"refusing to scaffold into non-empty folder: {root}")
    else:
        if not root.exists():
            sys.exit(f"{root} does not exist: create the {a.engine} project first, then scaffold inside it")
        if (root / "_project").exists():
            sys.exit("_project/ already exists here: refusing to overwrite")

    # (godot-style key, engine path) pairs
    keys = BASE + TYPES[a.type] + (["network", "ui/room"] if networked else [])
    if a.engine == "godot":
        keys += ["addons"]
        pairs = [(k, k) for k in keys]
    elif a.engine == "unity":
        pairs = [(k, "Assets/Game/" + pascal(k)) for k in keys if k != "tests"] + [("tests", "Assets/Tests")]
    else:
        content = [k for k in keys if k not in ("tests", "network")]
        pairs = [(k, "Content/" + pascal(k)) for k in content]
        pairs += [(k, f"Source/{game}/" + pascal(k)) for k in keys if k in ("network", "shared", "tests")
                  or k.split("/")[0] in ("levels", "characters", "objects", "ui", "vehicles", "weapons", "tracks", "maps", "units", "buildings", "board")]
    pairs.append(("_project", "_project"))

    for _, ep in pairs:
        d = root / ep
        d.mkdir(parents=True, exist_ok=True)
        if a.engine != "godot":
            (d / ".gitkeep").touch()
    (root / "_project" / "evidence").mkdir(parents=True, exist_ok=True)

    ctx = {"NAME": a.name, "TYPE": a.type, "NET": a.net, "GODOT": ev, "ENGINE": ENGINE_NAMES[a.engine],
           "ENGINE_NAME": f"{ENGINE_NAMES[a.engine]} {ev}" + (", GDScript" if a.engine == "godot" else ""),
           "ENGINE_BLOCK": ENGINE_BLOCKS[a.engine].replace("{V}", ev)}
    for doc in ["GAME_VISION.md", "STYLE_BIBLE.md", "DECISIONS.md", "CREDITS.md", "TOOLCHAIN.md"]:
        (root / "_project" / doc).write_text(fill((HERE / doc).read_text(), ctx))
    if a.engine == "godot" or not (root / ".gitignore").exists():
        shutil.copy(HERE / "gitignore.txt", root / ".gitignore")

    if not a.no_agents:
        (root / ".claude" / "agents").mkdir(parents=True, exist_ok=True)
        for f in AGENTS.glob("*.md"):
            shutil.copy(f, root / ".claude" / "agents" / f.name)

    if a.engine == "godot":
        for f in ["events.gd", "state.gd", "toon.gdshader"]:
            shutil.copy(HERE / f, root / "shared" / f)
        shutil.copy(HERE / "main_menu.gd", root / "ui/main_menu/main_menu.gd")
        (root / "ui/main_menu/main_menu.tscn").write_text(
            '[gd_scene load_steps=2 format=3]\n\n'
            '[ext_resource type="Script" path="res://ui/main_menu/main_menu.gd" id="1"]\n\n'
            '[node name="MainMenu" type="Control"]\nlayout_mode = 3\nanchors_preset = 15\n'
            'anchor_right = 1.0\nanchor_bottom = 1.0\nscript = ExtResource("1")\n')
        autoloads = ['Events="*res://shared/events.gd"', 'State="*res://shared/state.gd"']
        if networked:
            shutil.copy(HERE / "net_enet.gd", root / "network" / "net.gd")
            shutil.copy(HERE / "net_smoke.gd", root / "tests" / "net_smoke.gd")
            autoloads.append('Net="*res://network/net.gd"')
        (root / "project.godot").write_text(
            "config_version=5\n\n[application]\n\n"
            f'config/name="{a.name}"\nrun/main_scene="res://ui/main_menu/main_menu.tscn"\n'
            f'config/features=PackedStringArray("{ev}")\n\n[autoload]\n\n' + "\n".join(autoloads) + "\n")

    seams = {"godot": ("shared/events.gd (Events)", "shared/state.gd (State)", "network/net.gd (Net)"),
             "unity": ("an Events static class (Events)", "a GameState class (State)", "NetService.cs (Net)"),
             "unreal": ("an Events world subsystem (Events)", "the AGameStateBase subclass (State)", "a Net game-instance subsystem (Net)")}[a.engine]
    lines = [f"# Architecture - {a.name}", "", f"Engine: {ENGINE_NAMES[a.engine]} {ev}. Folder = category. Each folder holds its own scene/prefab, script and models.", "", "## Folders", ""]
    for gk, ep in sorted(pairs, key=lambda x: x[1]):
        if gk in DESC:
            lines.append(f"- `{ep}/` - {DESC[gk]}")
    lines += ["", "## Shared seams (the only abstraction allowed)", "", f"- {seams[0]}: signal bus.", f"- {seams[1]}: phase and score."]
    if networked:
        lines.append(f"- {seams[2]}: all multiplayer.")
    lines += ["", "## Where do I find...", "", "| I want to change... | Open |", "|---|---|", "| the title screen | ui/main_menu |",
              "| game phase / score | the State seam |", "| the look of everything | shared/ (shader + palette) |"]
    if networked:
        lines.append("| joining / room codes | the Net seam |")
    lines += ["| <<add a row per new script>> | |", "", "## How do I add a new...", "", "<<FILL a 5-line recipe per repeatable content type>>", ""]
    (root / "ARCHITECTURE.md").write_text("\n".join(lines))
    if not (root / "README.md").exists():
        (root / "README.md").write_text(f"# {a.name}\n\n<<FILL one-line pitch>>\n\n## Run\n<<FILL for {ENGINE_NAMES[a.engine]} {ev}>>\n\n## How to play\n<<FILL>>\n\n## Where things are\nSee ARCHITECTURE.md. Design docs are in _project/.\n")
    print(f"Created {a.type} project '{a.name}' ({a.engine} {ev}, net={a.net}) at {root}")
    if a.engine != "godot":
        print("Note: no engine code stubs were generated; create Events/State/Net per references/engines.md section 4.")
    print("Next: fill _project/GAME_VISION.md, then run scripts/check_project.py" + (" and scripts/gate_boot.sh" if a.engine == "godot" else ""))

main()
