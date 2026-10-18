---
name: game-builder
description: Build complete, playable, human-readable games with an AI agent using one fixed architecture, one code style, a vetted free toolchain ($0 budget), and a per-genre playbook. Use this skill whenever the user wants to make, prototype, extend, vibe-code, review or structure a game of ANY type (party/co-op "friendslop", platformer, shooter, racing, puzzle, strategy, survival, visual novel, arcade), solo or multiplayer, 2D or 3D, with Godot, Unity or Unreal Engine 5, Blender MCP, MCP servers and agent skills for game engines, free CC0 assets, room-code or peer-to-peer multiplayer, proximity voice chat, a style bible, game vision doc, folder architecture, asset pipeline or QA checklist. Trigger even on loose requests like "make me a game", "I want to play with friends", "help me structure my Godot project", or "turn this game idea into something playable".
---

# Game Builder

One standard for building games with an agent so the result is **fun, simple, consistent, and readable by a human who does not
know the engine**. Default engine: Godot 4 with GDScript. The principles are engine-neutral and `references/engines.md` maps them onto **Unity** and **Unreal Engine 5**; the runnable scripts and code templates are Godot-specific (scaffold and checker also work for Unity/Unreal folders and docs).

## Why these rules exist
Agent-built games fail in predictable ways, and each rule below answers one:
- The agent **guesses the game** -> a vision doc must exist first.
- It **over-builds** (abstractions, many documents, many tools) -> size caps, three seams, one measured finding that a heavy process ranked
  last on play quality against a one-page brief.
- Assets from different sources **clash** -> one palette, one shader, a lineup gate.
- It declares victory after a **parse check** -> gates that require running the game and seeing it.
- It ignores what **players actually do** (disconnect, spam, fall out of the world) -> edge-case lists per genre.
- It **re-researches tools** every session -> research once, pin it.

## Step 0: Classify the game (ask only what is missing)
Collect these answers (the first five are expensive to reverse). If the user's message does not give one, ask **only** for the missing ones, offering 2-3 options with
a recommendation (use the ask-user tool if available).

| # | Question | Decides | Read |
|---|---|---|---|
| 1 | **Game type**: party-coop / platformer / shooter / racing / puzzle / strategy / survival / narrative / arcade (or hybrid) | Folders, feel rules, edge cases, scope cap | `references/genres.md` (that section only) |
| 2 | **Players**: single / local / LAN / online rooms / web | Networking mode | `references/networking.md` |
| 3 | **Look**: 2D or 3D, and style (recommend low-poly flat for 3D) | Style bible, asset pipeline | `references/assets.md` |
| 4 | **Platform**: PC / web / mobile | Renderer, input, budgets | `references/genres.md` cross-cutting table |
| 5 | **Engine**: Godot (default) / Unity / Unreal | Toolchain, vocabulary, scripts available | `references/engines.md`, then `references/tools-<engine>.md` |

These four are **expensive to reverse**. Everything else (colors, key bindings, timers, prop placement) is **cheap**: decide it
yourself and log it in `_project/DECISIONS.md`. Never ask a question the user already answered, and never ask more than three at once.

## Workflow: phases with exit gates
Do not start a phase before the previous gate passes. Keep each phase small.

1. **Intake.** Fill `_project/GAME_VISION.md` from the user's answers. Exit: no `<<FILL>>` left in it; 30-second and 60-second tests written.
2. **Toolchain.** Read `references/toolchain.md` and the `tools-<engine>.md` for the chosen engine, verify the latest stable engine version and tool status, write `_project/TOOLCHAIN.md`.
   Install ONE editor-control MCP for the engine, Blender MCP, and the `awesome-gamedev-agent-skills` bundle for the engine. Decide voice chat now if the game needs it. Exit: versions pinned, free-tier limits recorded, $0 confirmed.
3. **Style.** Fill `_project/STYLE_BIBLE.md`, create the shared palette, shader, and `_project/lineup.tscn`. Exit: a screenshot of the lineup in `_project/evidence/`.
4. **Skeleton.** Run `python scripts/scaffold.py --name ... --type ... --net ... --path ... [--engine godot|unity|unreal]` (Unity/Unreal: create the project in the engine first, scaffold inside it). It also installs the nine agents into `.claude/agents/`. Build menu, (room), an empty level, and for networked games
   two instances connected. Exit: **G1** (`scripts/gate_boot.sh`), plus **G4** (`scripts/net_test.sh`) if networked.
5. **Vertical slice.** One level, one full loop, fully playable (and networked if applicable). Exit: **G2** screenshot, **G3** tests for rules, 30/60-second tests pass.
6. **Content.** Add one category at a time (new shop, enemy, track...). Each addition: lineup gate, `CREDITS.md` row, `ARCHITECTURE.md` row. Exit per addition: G1.
7. **Hardening.** Edge-case pass from `references/qa.md` and the genre list, performance pass, `scripts/check_project.py` with no errors. Exit: **G5**.
8. **Handover.** README, `ARCHITECTURE.md` "where do I find X" table and "how do I add a new..." recipes, header comments everywhere. Exit: release checklist in `references/qa.md`.

Show the user a short status after each phase (what works, what you decided, anything you need from them). Do not narrate every step.

## Non-negotiables (details in `references/standard.md`)
1. **Folder by category, self-contained.** Scene, script and models of a category live together. `ARCHITECTURE.md` always matches the tree.
2. **One compact script per category** (`shop1objs.gd`, `vehicles.gd`). Abstraction only at three seams: `Net`, `State`, `Events` (max 3 autoloads).
   Repetitive logic stays repeated, with a comment naming its siblings. Promote to a seam only after the same fix lands in three siblings.
3. **Simplest code that works.** Order: engine built-ins, then a pinned vetted addon, then short custom code. About 20 lines per function, 300 per file,
   a header comment (WHAT / TALKS TO / SIBLINGS) on every script, tunables as `@export`.
4. **One look.** Palette + shader + lineup gate. Nothing enters the game that does not fit.
5. **$0.** No paid services, servers or assets. If something cannot be done free, say so and offer the nearest free alternative.
6. **Licenses.** CC0 first. Every external asset has a `CREDITS.md` row the moment it enters the repo.
7. **Edge cases first-class.** Write down what a clumsy, hostile or unlucky player can do, then handle it.
8. **Evidence over claims.** "Done" means gates passed and the game was seen running. A parse check is not a run.
9. **Host-authoritative multiplayer**, all in `network/net.gd`, using the tested template.

## Tools and scripts
- `scripts/scaffold.py` creates the folder tree, docs and agents for any engine; for Godot also autoloads, a booting main menu, and (if networked) the tested `net.gd` and smoke test.
- `scripts/check_project.py <project>` enforces headers, size caps, documented folders, credits ledger (and the autoload cap and function length for Godot). Auto-detects Godot, Unity, Unreal.
- `scripts/gate_boot.sh <project>` = G1 and `scripts/net_test.sh <project>` = G4 (Godot only; Unity/Unreal commands are in their tools files). Set `GODOT=/path/to/godot` if it is not on PATH.
- Templates in `assets/templates/`: project docs, `net_enet.gd`, `net_smoke.gd`, `events.gd`, `state.gd`, `toon.gdshader`.
- If you are not in an environment with Godot installed (e.g. plain chat), produce the docs, structure, scripts and instructions, state clearly that gates G1-G4
  were not run, and tell the user how to run them.

## Reference index (read only what the task needs)
| File | Read when |
|---|---|
| `references/standard.md` | Always, once per project: the full cleaned rule set with examples, including how contradictions were resolved |
| `references/genres.md` | Step 0 and every time scope or feel is in doubt: only the matching section |
| `references/networking.md` | Any game with more than one player |
| `references/architecture.md` | Laying out or growing the folder tree, explaining it to a reviewer |
| `references/assets.md` | Choosing a style, adding any model/sound/texture, using Blender MCP |
| `references/qa.md` | Running gates, writing tests, edge-case pass, release |
| `references/toolchain.md` | Phase 2: index and rules for adopting tools |
| `references/tools-godot.md`, `tools-unity.md`, `tools-unreal.md` | Phase 2 and whenever a tool question comes up: MCP servers, skills per phase, networking, voice, testing, release, verdicts |
| `references/tools-general.md` | Blender MCP, asset sources and licenses, skill catalogs, agent lists, rejected tools |
| `references/engines.md` | Choosing an engine; mapping the standard onto Unity and Unreal |
| `references/agents.md` | Delegating steps to the nine custom agents (copied to `.claude/agents/` by the scaffold) |

## When the user's request conflicts with the standard
The user's explicit design choice wins; the standard wins on structure and process. If the user wants something that breaks a rule (e.g. a fourth autoload,
paid hosting, Unity), state the cost in one sentence, offer the compliant alternative, and follow their decision. Log it in `DECISIONS.md`.
