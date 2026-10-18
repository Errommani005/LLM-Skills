# Godot Toolchain (verified October 2026)

Read at Phase 2 (Toolchain) for any Godot project. Everything here was checked against its repository or docs in October 2026;
stars and versions drift, so re-check the **bold facts** before pinning in `_project/TOOLCHAIN.md`.

Pin: **Godot 4.7.1 stable** (4.7 released June 2026, 4.7.1 July 2026). Language: GDScript (C# only if the user insists).

## Contents
1. Editor control (MCP): pick ONE, optionally add ONE runtime tool
2. Knowledge skills to load per workflow phase
3. Assets and Blender
4. Networking and voice
5. Testing and gates
6. Build and release
7. Verdict summary

---

## 1. Editor control (MCP)

The agent needs a way to run the project, read errors, and edit scenes. **Install one editor-control server.** Two editor servers fight
over the same connection and confuse the agent.

| Server | Level | License / cost | Notes |
|---|---|---|---|
| **Coding-Solo/godot-mcp** (default) | Editor: launch editor, run project, capture debug output, create scenes, add nodes, load sprites, export MeshLibraries, UIDs | MIT, free, about 5.6k stars | Zero addon; needs Node.js 18+. Best free start for the stock editor |
| **hi-godot/godot-ai** | Editor-live: broad toolset over a WebSocket editor plugin + Python server | MIT, free; one-click config for 19+ clients | Newest big option, from the makers of MCP for Unity. Takes an addon committed into the project. Good second choice |
| **n24q02m/better-godot-mcp** | File-level: parses `.tscn`, edits scripts, 17 composite tools, `doctor` health check | MIT, free, small | Works with the editor closed. Use when you only need file edits |
| **Erodenn/godot-mcp-runtime** | Runtime bridge: injects a temporary TCP autoload to inspect the running game, auto-cleans | MIT, free, small | Add *beside* an editor server when you need to inspect a running game |
| tugcantopaloglu/godot-mcp, satelliteoflove/godot-mcp | Runtime / debugger-protocol options | MIT, free | Alternatives to the line above |
| **masteryee-labs/Open-Godot-MCP** | Deterministic playtesting, multiplayer testing, DAP debugging, LSP | MIT, free; `pip install open-godot-mcp` | Very new (July 2026) and its built-in vision/image tools call third-party APIs: treat as experimental, review before adopting |
| Godot MCP Pro ($15), GDAI MCP ($19), StraySpark (commercial) | Polished paid servers | Paid | **Rejected: breaks $0** |

Install (default):
```
claude mcp add godot -e GODOT_PATH=/path/to/godot -- npx @coding-solo/godot-mcp
```
For the others follow each repository's README (commands change); record the exact command you used in `TOOLCHAIN.md`.
No MCP at all still works: the scripts in `scripts/` run Godot headless from the command line (gates G1 and G4).

## 2. Knowledge skills to load per workflow phase

Source: `gamedev-skills/awesome-gamedev-agent-skills` (Apache-2.0, 74 skills, router, **version-pinned to Godot 4.7**).
```
npx skills add gamedev-skills/awesome-gamedev-agent-skills
# or, Claude Code plugin form, smaller:
claude plugin marketplace add gamedev-skills/awesome-gamedev-agent-skills
claude plugin install router@awesome-gamedev-agent-skills
claude plugin install godot@awesome-gamedev-agent-skills
```
The router detects `project.godot` and loads only what the task needs. **Precedence: this skill's structure rules win** (folders, three seams, size caps);
companion skills supply engine API detail only.

| Workflow phase | Godot skills to load | Cross-engine skills to load |
|---|---|---|
| 3 Style | `godot-shaders`, `godot-3d-essentials` | `create-game-assets`, `shader-programming` |
| 4 Skeleton | `godot-gdscript`, `godot-nodes-scenes`, `godot-signals-groups`, `godot-multiplayer` (if online) | `input-systems`, `game-ui-ux` |
| 5 Vertical slice | `godot-physics`, `godot-animation`, `godot-audio`, `godot-ui-control`, `godot-resources` | `game-feel`, `camera-systems`, `level-design`, `prototype-fast`, the matching genre skill |
| 6 Content | `godot-resources`, `godot-tilemap` (2D) | `save-systems`, `game-ai`, `procedural-gen`, `audio-design` |
| 7 Hardening | `godot-gdscript-headless-testing` | `physics-tuning`, `performance-optimization` |
| 8 Release | `godot-export` | `itch-publish` or `steam-publish` |

Genre skills available: platformer, roguelike, rpg, fps-shooter, tower-defense, card-game, visual-novel, survival-crafting, puzzle.
There is no racing or party-game genre skill: use `references/genres.md` for those. `godot-csharp` only if the project uses C#.

## 3. Assets and Blender
See `tools-general.md` for Blender MCP, free sources and licenses. Godot specifics: export `.glb`; use the `-col` / `-colonly` / `-convcolonly`
import suffixes; one shared `ShaderMaterial` (template `assets/templates/toon.gdshader`); `Compatibility` renderer for web and low-end GPUs.

## 4. Networking and voice

**Networking.** Built in and free: `ENetMultiplayerPeer`, `MultiplayerSpawner`, `MultiplayerSynchronizer`, RPCs. Use the tested template
`assets/templates/net_enet.gd` (host-authoritative listen server, room codes, edge cases handled). See `networking.md`.

**Voice chat.** Godot has **no built-in Opus encoder** (an open engine proposal), so voice needs an addon. Verified options:

| Option | Fit | Notes |
|---|---|---|
| **goatchurchprime/two-voip-godot-4 ("TwoVoip")** (recommended) | Proximity-capable | MIT, 178 stars, 338 commits. GDExtension with Opus compression, RNNoise denoise, voice-activation gating, jitter buffer, packet reordering. Builds for all six Godot platforms; on the Godot Asset Store. Transport-agnostic: the mic emits packets, **you send them through `Net`**, the speaker plays them. Put the speaker in an `AudioStreamPlayer3D` for positional/proximity sound |
| thegatesbrowser/godot-multiplayer | Reference template | MIT: third-person controller + positioned voice using TwoVoip. Study it for wiring |
| jam-launch/jam-voip + GodOpus | Reference | MIT: Opus voice over Godot RPC |
| modcommunity/dot-voice | Pure GDScript | MIT: push-to-talk or voice activation, per-speaker jitter buffer, routing to all / team / proximity; codec is pluggable (no Opus in plain GDScript) |
| one-voip-godot-4 | Superseded | Its own README points to TwoVoip |

If none work in the target build, the $0 fallback is "players use Discord" plus an in-game visual speaking indicator. See `networking.md` section 11.

## 5. Testing and gates
- **G1/G4:** `scripts/gate_boot.sh`, `scripts/net_test.sh` (headless Godot, tested here on 4.7.1).
- **G3:** GUT 9.x, `godot --headless -s addons/gut/gut_cmdln.gd -gdir=res://tests -gexit`; skill `godot-gdscript-headless-testing` covers exit codes for CI.
- **G2 (seeing the game):** the editor MCP's run/screenshot tools, or the one-line viewport capture in `qa.md`.
- Optional: Open-Godot-MCP for scripted playtests; gdmutant for mutation testing once tests exist.

## 6. Build and release
Export presets committed in `export_presets.cfg`; headless export per `godot-export`. itch.io is the $0 distribution path (`butler`, skill `itch-publish`);
Steam has a one-time fee and is the user's call (`steam-publish`).

## 7. Verdict summary
**Adopt:** Godot 4.7.x, Coding-Solo/godot-mcp, awesome-gamedev-agent-skills (godot + router), TwoVoip, GUT, this skill's scripts.
**Use with care:** hi-godot/godot-ai (alternative editor server), runtime MCPs, Open-Godot-MCP, dot-voice.
**Reject:** every paid Godot MCP, one-voip-godot-4 (superseded).
