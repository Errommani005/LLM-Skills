# Worked Example: Mall Stormers (Godot)

This is a complete deliverable produced with this skill, for the "Mall Stormers" friendslop game. It is both a format exemplar and the checker's test input.
Everything between the lines below is the prompt as it would be handed to the coding agent.

---

# Mall Stormers: Build Prompt

You are the coding agent that builds this game. Read this whole document first. The user's instructions below are requirements, not suggestions.
Tags: **[ASK]** = stop and ask the user before proceeding, do not guess. **[DEFAULT]** = a proposed default: use it, log it in `DECISIONS.md`, change only with a reason.
Anything not specified here is **yours to decide** (§3.3): decide it, keep it simple, and log it.

---

## PART 1: THE GAME

### 1.1 Pitch
"Mall Stormers" is a friendslop game: you and your friends storm a mall or shopping center and eat as many items as possible. Whoever ate the most calories before the time limit wins.
The game offers several different malls and shopping centers for variety.

### 1.2 Objective and rules
- Everything has a calorie value, not just food: food, shampoo, pens, laptops, and so on. Eat as many items as fast as possible.
- The match has a time limit. The player with the most calories eaten when it ends wins.
- An active **leaderboard** shows live standings during the match.

### 1.3 Core mechanics
**Weight brackets**
- The more you eat, the closer you get to the next weight bracket.
- Crossing a bracket makes your character model fatter and your movement slower and sluggier.

**Items**
- Every item has a calorie amount and realistic physics: it can be **held, eaten, and thrown**.
- Some items make the game easier or more chaotic and fun: hoverboards, skateboards, open water bottles, cans, and similar.
- Cans and bottles can be **opened**. An open one splashes liquid on the floor or on other players.
- Liquid on the floor makes the ground **slippery for 30 seconds**.

**Knockdown**
- A player who is knocked back or slips is **down for 3 seconds**, then gets up.
- On getting up they have **knockback and slip immunity for 15 seconds**.

**Sound**
- Every item consumption and every fall or throw impact has a sound effect appropriate to the object and what is happening to it.

**Voice and social**
- **Proximity voice chat**: nearby players hear each other (see §2.5 for the $0 approach).

### 1.4 Content
**Malls**
- Each mall has **specific, fixed shop positions** and its own realistically varied architecture. The mall's general architecture never changes between matches.
- **Shops are randomized every match**: placed fully at random on the mall's shop positions, so going to a specific spot will not lead to the same shop twice.
- Randomization must be flawless: no clipping, no empty or unfinished space, no immersion-breaking bugs or visual defects. Unacceptable otherwise.
- **Stairs, escalators and elevators** are fully functional.
- Mall walls and aesthetics are accurate and realistic for the setting. Shopfronts match their type: restaurants have themed chairs and tables in front of them, pharmacies have pharmacy signs in front of them, and so on.

**Shops**
- Each shop is designed realistically and differently from the others, like a real store.
- Items are on the correct shelves, placed realistically and properly.

### 1.5 Interface
Simple, goofy, unintrusive. It must never overwhelm the player and must fit the game's style and vision.

### 1.6 Fun and clarity (hard requirement)
The game must be simple to understand, fun, fast and engaging. No design decision may hurt how it plays, hurt engagement, or make it confusing.
It must pass the 30-second test (a new player states the goal without reading text) and the 60-second test (first moment of fun within a minute), see §2.8.

---

## PART 2: HOW TO BUILD IT

### 2.1 Engine and language
Godot 4.7.x, GDScript. Chosen with the user (recommended for a simple, goofy, low-poly, friends, $0 project).

### 2.2 Vision and style
- One fixed vision and one visual style. **No model, shader or visual deviation is accepted.** No asset may be made that does not fit the aesthetic.
- Style options: low poly 3D, simple-geometry 3D (Fall Guys / Among Us style), goofy old-school 3D (Goat Simulator style). The user leans toward low poly or simple geometry.
  [ASK] Recommend the best for this vision and for ease of agentic implementation, with reasons, and wait for confirmation before producing assets (§3.1).
- Lineup gate: every new asset is placed beside existing ones under the shared shader and palette, and is rejected if it does not fit.

### 2.3 Assets
- Use free, publicly available models and assets as much as possible. Make the rest with **Blender MCP** (and Blender-related AI design and rigging tools for what remains).
- Sourcing order: engine primitives, CC0 packs, Blender MCP builds, generative AI last. Keep a license ledger (`CREDITS.md`).
- Export `.glb`; one shared palette and shader.

### 2.4 Tools and research
- Research tools, skills, agent configurations and full coding tools for vibe-coding games and game assets. Use only the highest-quality, most developed ones; do not waste time on ones you judge unfit; never compromise quality.
- Tools the user named: https://genex.games/desktop (web/Three.js only: skip for Godot), https://github.com/gamedev-skills/awesome-gamedev-agent-skills (use), https://www.scenario.com/ (2D only: skip),
  https://github.com/Donchitos/Claude-Code-Game-Studios (mine for ideas only), https://github.com/Coding-Solo/godot-mcp (use).
- Verify the tool references in Part 4 are current, then pin the result once in `_project/TOOLCHAIN.md`.

### 2.5 Multiplayer and budget
- Peer-to-peer rooms for playing with friends: one friend hosts, the others join with a room code. Host-authoritative: clients send requests, the host decides.
- **The budget is $0.** No paid service, API or tool. Build everything cleanly and completely: assets, mechanics and backend.
- Risky at $0, with approach and fallback: **voice chat** (use the vetted free Godot addon in Part 4; fallback Discord plus a speaking indicator) and **reaching hosts across the internet** (LAN, free VPN overlay, UPnP, or port forwarding; some pairs may fail, so show a clear message).
- The final game must be engaging, fun, optimized and bug-free.

### 2.6 Architecture (enforced; a human with no Godot experience will review this)
- **Folder by category.** Each category folder contains its own technical parts (scene, script, models), so the tree is easy to navigate:
```
levels/       one folder per level, each holding its areas (mall1/ -> shops/shop1/ {shop1.tscn, shop1objs.gd, models/})
objects/      items shared across levels: scene + script + models together
characters/   players/ (player.tscn, players.gd, models/), enemies/
ui/           main_menu/, room/, hud/, game_over/, victory/, settings/
network/      net.gd (all multiplayer), roomlogic.gd
shared/       palette, the one shader, state.gd, events.gd
audio/ addons/ tests/ _project/   (docs: vision, style bible, decisions, credits, toolchain)
```
- **One compact script per trackable category of objects**, containing everything about it including physics. Example names: `shop1objs.gd`, `shop2objs.gd`, `vehicles.gd`, `players.gd`, `roomlogic.gd`, `mall1.gd` (connected to shop1, shop2, shop3 and so on).
- **Do not over-modularize.** Use abstraction only where things change a lot and link to other things: networking (`net.gd`), game state (`state.gd`) and events (`events.gd`). Static or repetitive logic (object physics, shading) stays as plain repeated code in its own scripts, each with a comment naming its siblings.
- Keep `ARCHITECTURE.md` with a one-line description per folder and a "where do I find X" table, plus a "how do I add a new shop/mall/item" recipe.

### 2.7 Code style
- Simplest, shortest logic: write like a beginner who writes bug-free code. The fewest instructions that do the most work, not the most instructions that do the least.
- Priority: engine built-ins, then proven vetted libraries and scripts, then custom code, all in one consistent scripting structure and style.
- About 20 lines per function and 300 per file; a header comment (WHAT / TALKS TO / SIBLINGS) on every script; tunable numbers exposed at the top.

### 2.8 Execution rules
**Phases.** Work in phases, each ending with something demoable and a short report (done, deferred, open questions):
1 Intake (read this, resolve [ASK] items), 2 Toolchain (§2.4), 3 Style (style bible, shared palette and shader, lineup scene), 4 Skeleton (menu, room, empty mall, two instances connected),
5 Vertical slice (one mall, three shops, the full eat/throw/slip loop, fully playable), 6 Content (more shops and malls, one category at a time), 7 Hardening (edge cases, performance), 8 Handover (README, `ARCHITECTURE.md`, recipes).
**Gates** (a phase is done only when they pass; a parse check is not a run):
G1 the project boots with zero script errors; G2 the game is launched and the key screen is seen (screenshot saved); G3 rules with numbers or state (calories, brackets, immunity timers) have tests;
G4 two real instances connect and finish a match, including full room, late join, host leaving and duplicate names; G5 the edge-case list below is ticked or logged.
**Edge cases.** For every mechanic write what a clumsy, hostile or unlucky player could do and handle it. Game-specific list:
two players grab one item; an item is destroyed or falls out of the world while carried; a carrier disconnects (drop the item); a player is stuck or falls out (respawn at spawn point);
liquid on stairs, escalators and lifts; thrown items hitting down or immune players; eating an item that is also being held by another player; a match ending mid-throw;
shop randomization producing overlaps or empty slots (validate every combination or a large random sample); the last player left in a room.
**Decisions.** Ask only about [ASK] items and choices that are expensive to reverse; decide cheap ones and log them in `DECISIONS.md` (id, decision, reason, reversible?).
**Companion skill.** If the `game-builder` skill is available, use it for the workflow, scaffold and gate scripts. This document stays authoritative.

### 2.9 Definition of done
Complete and fully playable from a fresh launch; all gates pass; `CREDITS.md` covers every external asset; a friend who never saw the game can play a full match without help.

---

## PART 3: DECISIONS AND ASSUMPTIONS

### 3.1 [ASK] before building
1. [ASK] Visual style: low poly, simple geometry, or goofy old-school (recommendation required, §2.2).
2. [ASK] Players per room: proposed 2 to 6.
3. [ASK] Camera: proposed third person.
4. [ASK] Platform: proposed Windows and Linux PC builds at 60 FPS on integrated graphics.
5. [ASK] Voice chat: confirm the free addon approach and the Discord fallback (§2.5).
6. [ASK] Connectivity: confirm host plus room code reached over LAN, VPN, UPnP or port forward.

### 3.2 [DEFAULT] proposed values
- [DEFAULT] Match length 5 minutes, with a countdown and a final-30-seconds warning.
- [DEFAULT] Tie-break: the player who reached the tied calorie total first.
- [DEFAULT] 5 weight brackets, each with a visible model change and a speed multiplier; the numbers live in one table at the top of `players.gd`.
- [DEFAULT] Shop randomization by size class: every shop slot has a class (small, medium, large) and every shop scene is built to fit its class exactly with matching door positions; each mall keeps a pool large enough to fill all its slots.
- [DEFAULT] Shop decoration (signs, themed furniture) belongs to the shop scene and moves with it.
- [DEFAULT] Shelves are stocked at match start; items respawn slowly so the mall never empties.
- [DEFAULT] A short spawn protection at match start; the 15-second immunity prevents repeated knockdown.
- [DEFAULT] Host leaves: the room closes and everyone returns to the menu. Rooms close once the match starts (no late joiners).
- [DEFAULT] The results screen shows ranking, calories and a goofy title per player.

### 3.3 Decided by the builder (not specified here)
Gameplay tuning numbers, exact UI layout and art details within the confirmed style, item and shop lists, physics tuning, camera feel, sound selection, file-level code structure inside §2.6, test design, and every other detail not stated above.
Decide, keep it simple, and log it in `DECISIONS.md`.

---

## PART 4: TOOL REFERENCES (Godot)

```
ENGINE: Godot 4.7.x stable (verify the latest 4.7.x, then pin it). Language: GDScript.

EDITOR CONTROL (install ONE editor server; two fight each other):
- Default: Coding-Solo/godot-mcp (MIT, ~5.6k stars): launch editor, run project, read debug output, create scenes, add nodes.
  claude mcp add godot -e GODOT_PATH=<path to godot> -- npx @coding-solo/godot-mcp     (needs Node.js 18+)
- Alternative: hi-godot/godot-ai (MIT, WebSocket editor plugin, 19+ clients). Optional second tool for runtime inspection: Erodenn/godot-mcp-runtime (MIT).
- Do NOT use paid servers (GDAI MCP, Godot MCP Pro, StraySpark).

SKILLS (engine detail only; this prompt's structure rules win):
  npx skills add gamedev-skills/awesome-gamedev-agent-skills      (Apache-2.0, router + 16 Godot skills pinned to Godot 4.7)
  Useful: godot-gdscript, godot-nodes-scenes, godot-signals-groups, godot-physics, godot-3d-essentials, godot-shaders, godot-animation,
  godot-ui-control, godot-resources, godot-audio, godot-multiplayer, godot-export, godot-gdscript-headless-testing;
  cross-engine: game-feel, level-design, physics-tuning, performance-optimization, create-game-assets, audio-design, camera-systems, input-systems.

ASSETS: Blender MCP (ahujasid/blender-mcp, MIT):  DISABLE_TELEMETRY=true claude mcp add blender uvx blender-mcp    (Hyper3D generation stays off).
  Free sources, CC0 first: Kenney, Quaternius, KayKit, Poly Haven; Mixamo for humanoid animation. Export .glb; use Godot import suffixes -col / -colonly.

NETWORKING: Godot built-in high-level multiplayer (ENet), host-authoritative listen server, MultiplayerSpawner/Synchronizer. Room code = the host's address encoded
  as a short code; hosts are reached via LAN, a free VPN overlay (Tailscale/ZeroTier; verify free limits), UPnP, or port forwarding.
VOICE (only if required): TwoVoip (goatchurchprime/two-voip-godot-4, MIT): Opus + RNNoise + jitter buffer; send its packets through the networking script
  and play them from an AudioStreamPlayer3D on the speaker for proximity. Fallback: players use Discord + an in-game speaking indicator.

TESTS: GUT 9.x (headless: godot --headless -s addons/gut/gut_cmdln.gd -gdir=res://tests -gexit); headless boot check; two-instance multiplayer smoke test.
RELEASE: Godot export presets; itch.io via butler is the $0 path.

CUSTOM AGENTS (optional, for large builds): the nine step-specific agents of the game-builder skill (game-director, architect, gameplay-programmer, network-engineer,
tech-artist, level-builder, qa-edge-hunter, performance-profiler, handover-reviewer). General second-opinion agent: voltagent-domains:game-developer
(claude plugin marketplace add VoltAgent/awesome-claude-code-subagents; claude plugin install voltagent-domains).
IDEA SOURCES (read for ideas, do not adopt wholesale): Claude Code Game Studios (a heavy 30-document process ranked last on play quality in its own measurement),
Genex Desktop (web/Three.js only), Scenario (2D only, free tier unclear): none is required.
RESEARCH RULE: research tools once, at the start; verify each version, license and free-tier limit above is still current; pin the result in _project/TOOLCHAIN.md. Do not re-research later.
```
