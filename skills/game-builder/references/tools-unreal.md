# Unreal Engine 5 Toolchain (verified October 2026)

Read at Phase 2 (Toolchain) for any UE5 project. Facts marked **verify** were not confirmed against current official terms.

Pin: **Unreal Engine 5.8** (released June 2026; the companion skills are written against it). UE licensing: free to use with a royalty above a revenue threshold set by Epic:
**verify** current terms against the $0 rule before starting.

## Contents
1. Editor control (MCP)
2. Knowledge skills per workflow phase
3. Blueprint or C++ (an expensive decision: ask)
4. Assets
5. Networking and voice
6. Testing and gates
7. Build and release
8. Verdict summary

---

## 1. Editor control (MCP)

| Server | How it connects | License / cost | Notes |
|---|---|---|---|
| **ChiR24/Unreal_mcp (`unreal-engine-mcp-server`)** (default) | Editor plugin ("MCP Automation Bridge") serving MCP over local HTTP `:3000/mcp`; optional Node bridge on WebSocket `:8090` | **MIT, free; UE 5.0 to 5.8**; npm + MCP registry; wiki updated 2026-09-30 | Broadest version support among free options. Assistant finds tools by plain-word search |
| **Epic's official "Unreal MCP" plugin** | MCP server embedded in the editor over local HTTP | Free, ships with UE 5.8 | **Experimental.** Sources disagree on whether it needs a source build of the engine: check Epic's 5.8 release notes. Good to try first if you are already on 5.8 |
| **ATDev UEMCP (PyPI `uemcp`)** | Uses UE's **built-in Python remote execution**: nothing to compile or install in the project | Free; works on vanilla UE 5.0 to 5.6 | `claude mcp add unreal -- uvx uemcp`. 29 dedicated tools plus a raw `ue_python` escape hatch. Treat it like giving the agent the editor's Python console: use source control |
| GenOrca/unreal-mcp | C++/Python plugin | UE 5.6+; check the repo's license | Strong on Blueprint graphs, Behavior Trees, UMG widgets, materials, cinematics |
| IvanMurzak/Unreal-MCP | C++ plugin from Fab + a shared engine-agnostic server | Free, but **defaults to a hosted cloud backend** (ai-game.dev) unless you self-host | Cloud dependency: avoid unless self-hosted |
| Ludus AI, Fab "Claude Assistant" | Commercial | Paid | **Rejected: breaks $0** |

Install (default): follow the ChiR24 wiki ("About ten minutes from an empty project"): install the plugin into the project, enable it, open the editor, then point the MCP client at `http://localhost:3000/mcp` or the npm bridge. Record the exact steps in `TOOLCHAIN.md`.

Run **one** UE MCP server at a time.

## 2. Knowledge skills per workflow phase

- **`ibrews/ue5-mcp`**: a Claude skill, server-agnostic, covering engine-level behavior for UE 5.7 and 5.8 (Blueprints, Niagara, MetaSound, materials, pixel streaming, Python editor scripting). Install: `/plugin marketplace add ibrews/ue5-mcp` then `/plugin install ue5-mcp@ibrews-ue5-mcp`.
- **`gamedev-skills/awesome-gamedev-agent-skills`** has 6 Unreal skills pinned to UE 5.8:
  `unreal-blueprints`, `unreal-cpp-gameplay`, `unreal-enhanced-input`, `unreal-behavior-trees`, `unreal-niagara`, `unreal-packaging`.
```
npx skills add gamedev-skills/awesome-gamedev-agent-skills
claude plugin install router@awesome-gamedev-agent-skills
claude plugin install unreal@awesome-gamedev-agent-skills
```
| Workflow phase | Unreal skills | Cross-engine skills |
|---|---|---|
| 3 Style | `unreal-niagara` (effects), materials via `ue5-mcp` | `create-game-assets`, `shader-programming` |
| 4 Skeleton | `unreal-cpp-gameplay`, `unreal-blueprints`, `unreal-enhanced-input` | `input-systems`, `game-ui-ux` |
| 5 Vertical slice | `unreal-cpp-gameplay`, `unreal-niagara` | `game-feel`, `camera-systems`, `level-design`, genre skill |
| 6 Content | `unreal-behavior-trees` (AI) | `save-systems`, `game-ai`, `procedural-gen`, `audio-design` |
| 7 Hardening | (Automation, see section 6) | `physics-tuning`, `performance-optimization` |
| 8 Release | `unreal-packaging` | `itch-publish` / `steam-publish` |

**Gaps:** the catalog has **no Unreal networking skill** and no UE testing skill. Use Epic's replication documentation and section 5 below.

## 3. Blueprint or C++ (ask the user)

Blueprints are binary `.uasset` files: an agent can only edit them through the MCP, they diff badly, and a human reviewer needs the editor to read them. C++ is text, reviewable and diffable, but has compile times and a steeper start.
Recommended default for this standard: **C++ base classes for logic, Blueprint subclasses only for asset wiring and tuning values** (the standard Unreal pattern). Pure-Blueprint is acceptable for small, designer-driven projects if the user prefers it and accepts weaker reviewability.
Whichever is chosen, the folder, seam and header-comment rules still apply (see `engines.md`).

## 4. Assets
- **Fab** (successor to the Unreal Marketplace, Sketchfab Store and Quixel): Standard License is stated by Epic to work in any engine, but a third-party summary claims some free Megascans use is limited to Unreal: **read each asset's license**. The full free Megascans library ended 2024-12-31; a permanent free starter pack (over 1,500 assets) and a rotating free drop every two weeks remain.
- CC0 packs (Kenney, Quaternius, KayKit) import as FBX or glTF (Interchange).
- Blender MCP as in `tools-general.md`. Style gate: one master material with a palette texture and a Lineup level `/Game/_Lineup`.
- Prefer stylized low-poly. Nanite, Lumen and Megascans-scale realism are the opposite of "simple and goofy" and cost performance on integrated graphics: switch them off unless the vision needs them.

## 5. Networking and voice
- **Built in and free:** the replication framework (Actors, RPCs, `GameMode`/`GameState`/`PlayerState`), listen server, Online Subsystem Null for LAN. Host-authoritative is the engine's native model (the server owns the truth), so the standard's authority rules map directly.
- **Epic Online Services (EOS):** free-to-use SDK for sessions, P2P and voice (**verify** current terms): the standard $0 route past NAT.
- Voice: EOS Voice (**verify**), or ODIN by 4Players which has a sample project (pricing **unverified**). Fallback: Discord plus a speaking indicator.
- No networking skill exists in the catalog: read Epic's networking docs (Actor replication, RPCs, relevancy).

## 6. Testing and gates
- **G1 Boots:** build the editor target, then launch headless: `UnrealEditor-Cmd <project>.uproject -unattended -nullrhi -ExecCmds="quit"` and scan the log for `Error:` (**verify** flags for 5.8).
- **G3 Logic tests:** Automation Framework / Functional Tests, run with `-ExecCmds="Automation RunTests <Filter>; Quit"` (**verify**); Gauntlet for heavier orchestration.
- **G2 Screenshot:** `HighResShot` console command or the MCP's screenshot tool.
- **G4 Multiplayer:** launch the editor with 2+ clients (Play Settings: Number of Players, Net Mode "Play As Listen Server") plus a packaged two-machine test.

## 7. Build and release
`unreal-packaging` skill: cook and package (`RunUAT BuildCookRun`). itch.io via `butler` is the $0 path.

## 8. Verdict summary
**Adopt:** ChiR24/Unreal_mcp (or Epic's official plugin once stable), ibrews/ue5-mcp, awesome-gamedev-agent-skills (unreal + router), built-in replication, Fab free assets (license-checked).
**Use with care:** ATDev UEMCP (older versions, no C++), GenOrca/unreal-mcp, EOS (verify), ODIN.
**Reject:** Ludus AI, Fab "Claude Assistant" (paid), IvanMurzak/Unreal-MCP on its hosted backend.
