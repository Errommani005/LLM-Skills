# Engines: how the standard maps onto Godot, Unity and Unreal

The standard (`standard.md`) is engine-neutral. The scripts and templates are Godot-specific. This file shows the same rules in Unity and Unreal vocabulary
so the architecture, code style and gates stay identical whatever engine the user picks.

## Contents
1. Engine choice (ask, with a recommendation)
2. Vocabulary map
3. Folder layouts
4. The three seams
5. Code style per engine
6. Gates per engine
7. Networking default per engine
8. What the scripts do per engine

## 1. Engine choice
| Situation | Recommend |
|---|---|
| Default: small team or solo, friends multiplayer, beginner-reviewable code, $0 | **Godot 4 (GDScript)**: no build step, text scenes, smallest project |
| Wants C#, a huge asset store, existing Unity knowledge, mobile reach | **Unity 6.3 LTS (C#, URP)** |
| Needs high-end 3D visuals, large worlds, or the user already knows Unreal | **Unreal 5.8 (C++ base + Blueprint subclasses)**: heaviest to build, review and run |
| Browser-first, tiny scope | Three.js / Phaser (`awesome-gamedev-agent-skills` web-engines) |
This is an expensive-to-reverse decision. Always ask, recommend Godot for "simple, goofy, low-poly, friends, $0", and log it in `DECISIONS.md`.
Reviewability for a human new to the engine and agent-editability both favor text-based projects (Godot `.tscn`/`.gd`, Unity `.cs` plus YAML scenes, Unreal C++).

## 2. Vocabulary map
| Standard term | Godot | Unity | Unreal |
|---|---|---|---|
| Category script | `.gd` on the scene root | `.cs` MonoBehaviour on the prefab root | C++ `AActor`/`UActorComponent` class |
| Reusable object ("prefab") | Scene `.tscn` | Prefab `.prefab` | Blueprint subclass of a C++ class |
| Level | Scene | Scene `.unity` | Level `.umap` |
| Shared tunable | `@export var` | `[SerializeField]` field | `UPROPERTY(EditAnywhere)` |
| Data table | `Resource` `.tres` | `ScriptableObject` | `UDataAsset` / DataTable |
| Signal / event | `signal` | C# `event` or ScriptableObject channel | Delegate (`DECLARE_DYNAMIC_MULTICAST_DELEGATE`) |
| Group / find-all | node groups | tags or a registry list | Actor tags, or `GetAllActorsOfClass` once at BeginPlay |
| Kill plane | `Area3D` + body_entered | trigger collider | `KillZ` / trigger volume |

## 3. Folder layouts
Same rule everywhere: **folder by category, each folder self-contained, design docs in `_project/` at the repo root** (outside engine-imported folders).

```
GODOT   res://  _project/ levels/ characters/ objects/ ui/ network/ shared/ audio/ addons/ tests/
UNITY   <repo>/_project/   Assets/Game/{Levels,Characters,Objects,UI,Network,Shared,Audio}   Assets/Tests/   Packages/
UNREAL  <repo>/_project/   Source/<Game>/{Levels,Characters,Objects,UI,Network,Shared}   Content/{Levels,Characters,Objects,UI,Shared,Audio}   Plugins/
```
Unity: keep everything under `Assets/Game/` so imported plugins and samples do not mix with the game. Inside, each category folder holds its prefab, script and models together (`Assets/Game/Levels/Mall1/Shops/Shop1/Shop1Objs.cs`, `Shop1.prefab`, `Models/`).
Unreal: C++ lives in `Source/`, assets in `Content/`: mirror the same category names in both so a reviewer finds `Shop1` in both trees. Prefix assets by Epic's convention (`BP_`, `SM_`, `M_`) and keep that naming throughout.

## 4. The three seams
| Seam | Godot | Unity | Unreal |
|---|---|---|---|
| **Net** (all networking) | autoload `net.gd` | one `NetService.cs` wrapping NGO/Mirror, singleton in a bootstrap scene | a `UGameInstanceSubsystem` (`UNetSubsystem`) wrapping sessions |
| **State** (phase, score) | autoload `state.gd` | `GameState` plain C# class held by a bootstrap object | the engine's `AGameStateBase` subclass |
| **Events** (signal bus) | autoload `events.gd` | static C# events class, or ScriptableObject event channels | a `UWorldSubsystem` holding delegates |
Max three. Nothing else becomes a global.

## 5. Code style per engine
Same caps: about 20 lines per function, 300 per file, header comment (WHAT / TALKS TO / SIBLINGS) on every script, tunables exposed to the editor, plain names.
- **Unity C#:** one MonoBehaviour per file, file name equals class name, no custom base classes, no dependency-injection frameworks, no `Find`-by-string in `Update`; use `[SerializeField]` references, tags, and C# events. ScriptableObjects for data tables. Cache components in `Awake`.
- **Unreal C++:** one class per header/source pair, `UPROPERTY` for every tunable, no Blueprint spaghetti (if Blueprints are used for logic, keep graphs small and commented), no raw `new` (use `NewObject`/`CreateDefaultSubobject`), Epic's naming prefixes (`A`, `U`, `F`, `E`). Gameplay logic in C++; Blueprint for asset wiring.
- **Header comment syntax:** `#` in GDScript, `//` in C#/C++, same four lines.

## 6. Gates per engine
| Gate | Godot | Unity | Unreal |
|---|---|---|---|
| G1 Boots | `scripts/gate_boot.sh` | batch-mode compile and scan log for `error CS` | build editor target, run `UnrealEditor-Cmd` headless, scan log |
| G2 Seen | MCP run + screenshot | MCP screenshot / `ScreenCapture` | `HighResShot` / MCP screenshot |
| G3 Tests | GUT | Unity Test Framework | Automation / Functional Tests |
| G4 Multiplayer | `scripts/net_test.sh` | two builds / Multiplayer Play Mode | PIE with 2+ clients, listen server |
| G5 Edge cases | `qa.md` checklist | same | same |
Exact command lines for Unity and Unreal are in `tools-unity.md` / `tools-unreal.md` and are marked **verify** (not run in this environment).

## 7. Networking default per engine
Host-authoritative, 2-4 players for friend games, the same authority rules as `networking.md`:
- **Godot:** tested `net_enet.gd` template.
- **Unity:** NGO (or Mirror) host + clients; direct IP/LAN at $0; Relay only after verifying free limits; official `U6-First-Person-Multiplayer` sample as the reference.
- **Unreal:** built-in replication with a listen server; EOS for NAT traversal after verifying terms.
The edge-case list in `networking.md` section 7 applies to all three: re-implement and re-test each case in the chosen engine.

## 8. What the scripts do per engine
| Script | Godot | Unity | Unreal |
|---|---|---|---|
| `scaffold.py --engine X` | full project skeleton, booting menu, autoloads, net template | docs + `Assets/Game/` folders + `_project/` in an **existing** Unity project | docs + `Content/` + `Source/` folders + `_project/` in an **existing** Unreal project |
| `check_project.py` | headers, caps, autoload cap, folders, credits | headers (`//`), file-size cap, folders under `Assets/Game`, credits | headers, file-size cap, folders under `Content`, credits |
| `gate_boot.sh`, `net_test.sh` | yes | Godot only: use the engine commands above | Godot only: use the engine commands above |
Create the Unity or Unreal project in its own editor/hub first (the scaffold cannot generate engine project files), then run the scaffold inside it.
