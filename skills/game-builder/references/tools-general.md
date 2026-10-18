# Cross-Engine Tools (verified October 2026)

Tools that work with any engine: Blender, asset sources, skill catalogs, agent lists, and ideas worth borrowing. Engine-specific tools are in
`tools-godot.md`, `tools-unity.md`, `tools-unreal.md`.

## Contents
1. Blender MCP (custom assets)
2. Free asset sources and their licenses
3. Audio
4. Skill catalogs (cross-engine disciplines, genres, workflows)
5. Agent lists
6. Idea sources, not adopted
7. Rejected for the $0 rule
8. Choosing tools per workflow phase

## 1. Blender MCP
`ahujasid/blender-mcp` (MIT, about 12k stars): the agent runs Python inside Blender and reads the scene; has a Poly Haven integration (CC0 HDRIs and textures) and optional
Hyper3D generation.
```
DISABLE_TELEMETRY=true claude mcp add blender uvx blender-mcp
# In Blender: install the add-on, enable "Interface: Blender MCP", press "Connect to Claude" in the sidebar.
```
Needs Blender 3.0+ (4.x recommended) and `uv`. Run only one MCP server instance. It executes arbitrary Python in Blender: save your file and use version control.
**Hyper3D generation: off by default** (needs an API key; meshes rarely match a low-poly style). Workflow and glTF rules: `assets.md`.

## 2. Free asset sources and their licenses
| Source | License | Best for | Notes |
|---|---|---|---|
| **Kenney** (kenney.nl) | CC0 | Blocky low-poly 3D, 2D, UI, audio | The widest consistent CC0 base |
| **Quaternius** | CC0 | Animated rigged characters, nature | May not be resold or redistributed as a pack |
| **KayKit** | CC0 | Dungeon kits, characters | Consistent low-poly style |
| **Poly Haven** | CC0 | HDRIs, textures, some models | Realistic: use only if the style bible allows |
| Poly Pizza, Sketchfab (free) | Mixed CC0 / CC-BY | Gap filling | **Filter to CC0** or log the credit. Sketchfab's paid store moved to Fab |
| **Fab** | Per asset (Standard License, Creative Commons, free) | Unreal and Unity content | Epic says the Standard License works in any engine, but check each listing. Permanent free Megascans starter pack (over 1,500 assets) plus a rotating free drop every two weeks. Full Megascans free era ended 2024-12-31 |
| Unity Asset Store (free) | Unity-only | Unity projects | Cannot be extracted from a compiled game |
| Mixamo | Free with an Adobe account | Humanoid animation | Ship inside the game; never redistribute raw files |
Every asset gets a `CREDITS.md` row the moment it enters the repo.

## 3. Audio
Kenney audio packs (CC0); Freesound (check each file; prefer CC0); free generators such as jsfxr for blips; record foley yourself for item/impact sounds.
Names, buses and the settings screen: `assets.md` section 8. Per-engine audio skills: `godot-audio`, `audio-design` (cross-engine).

## 4. Skill catalogs
**`gamedev-skills/awesome-gamedev-agent-skills`** (Apache-2.0, 1.6k stars, 74 skills, router that detects the engine from `project.godot` / `*.uproject` / Unity project files).
```
npx skills add gamedev-skills/awesome-gamedev-agent-skills            # all engines; add --list to preview, -a claude-code to target
claude plugin marketplace add gamedev-skills/awesome-gamedev-agent-skills
claude plugin install router@awesome-gamedev-agent-skills             # plus: godot | unity | unreal | web-engines | other-engines
```
Cross-engine skills (load beside the engine skill):
| Group | Skills |
|---|---|
| Disciplines (15) | `create-game-assets` (art direction and production pipeline), `game-ai`, `ai-behavior-trees-utility-ai`, `procedural-gen`, `dialogue-systems`, `save-systems`, `audio-design`, `shader-programming`, `physics-tuning`, `level-design`, `input-systems`, `game-feel`, `game-ui-ux`, `camera-systems`, `performance-optimization` |
| Genres (9) | `platformer`, `roguelike`, `rpg`, `fps-shooter`, `tower-defense`, `card-game`, `visual-novel`, `survival-crafting`, `puzzle` |
| Workflows (4) | `game-jam`, `prototype-fast`, `steam-publish`, `itch-publish` |
Also covers web engines (Phaser 4.2, PixiJS 8.21, three.js r186), Bevy, pygame, LOVE and Roblox if the user picks one of them.
**Not in it:** racing and party-game genre skills, networking for Unity or Unreal, testing for Unity or Unreal, and voice chat.
Precedence: companion skills give API detail; **this skill's folder, seam, style and gate rules win**.

## 5. Agent lists
- **VoltAgent/awesome-claude-code-subagents**: plugin `voltagent-domains` includes **`game-developer`** (senior, engine-neutral: Unity, Unreal, Godot, Phaser, Pixi, Three.js; systems, rendering, networking, gameplay). Also useful: `code-reviewer`, `refactoring-specialist`, `agent-organizer`.
  ```
  claude plugin marketplace add VoltAgent/awesome-claude-code-subagents
  claude plugin install voltagent-domains
  ```
  It is general-purpose: it does not know this standard. Use it for second opinions; use the step-specific roster in `agents.md` for the build.
- **Step-specific roster:** `agents.md` and `assets/agents/` (nine agents, one per kind of workflow step, ready to copy into `.claude/agents/`).

## 6. Idea sources, not adopted
| Tool | Take | Leave |
|---|---|---|
| **Claude Code Game Studios** (49 agents, 72 to 74 skills) | Run-and-look evidence, design-before-code discipline, path-scoped coding rules | The agent hierarchy: its own measurement ranked a 30-document process last on play quality against a one-page brief |
| **Genex Desktop** (open source) | Useful only if the user picks a Three.js or other web-first engine | Not for Godot, Unity or Unreal |

## 7. Rejected for the $0 rule
Scenario (2D-only; its documents conflict on whether the free tier has credits); every paid MCP server and assistant (GDAI, Godot MCP Pro, StraySpark, Coplay MCP beyond beta, Aura, Ludus AI, Fab "Claude Assistant");
Photon Voice, Dissonance; dedicated server and relay hosting; Steam lobbies unless the user chooses to ship on Steam.

## 8. Choosing tools per workflow phase
| Phase | Tool class | Examples |
|---|---|---|
| 1 Intake | Discussion, no tools | `game-director` agent (read-only) |
| 2 Toolchain | Research once, pin it | `tools-<engine>.md`, `TOOLCHAIN.md` |
| 3 Style | Asset pipeline, shader, lineup | Blender MCP, `create-game-assets`, `tech-artist` agent |
| 4 Skeleton | Editor-control MCP + engine skills | Godot MCP / Unity MCP / Unreal MCP, `architect`, `network-engineer` |
| 5 Vertical slice | Engine skills + genre skill | `gameplay-programmer`, `game-feel`, `prototype-fast` |
| 6 Content | Level and asset production | `level-builder`, Blender MCP, free packs |
| 7 Hardening | Tests, profiling, edge cases | `qa-edge-hunter`, `performance-profiler`, test frameworks |
| 8 Handover | Review as a beginner | `handover-reviewer`, `check_project.py` |
