# Engine Profiles

One profile per engine. Each has: when to recommend it, the **vocabulary** to use in the prompt's architecture section, a **paste-ready Tool References block** (goes into Part 4 of the
deliverable prompt verbatim), and **$0 flags**. Facts verified October 2026; items marked *verify* were not confirmed against current official terms, so the prompt tells the builder to check them.

## Contents
1. How to choose and present the engine
2. Godot profile
3. Unity profile
4. Unreal profile
5. Cross-engine block (always appended)
6. Web-first alternative

## 1. How to choose and present the engine
The engine is the one decision that is truly expensive to reverse. Present it as a short table with a recommendation and one-line reasons, then ask the user to confirm:

| Engine | Choose when | Costs |
|---|---|---|
| **Godot 4 (GDScript)** | Simple/goofy/low-poly, friends multiplayer, $0, a reviewer who knows no engine | Smaller asset ecosystem; fewer polished AI helpers than Unity |
| **Unity 6.3 LTS (C#, URP)** | User wants C#, knows Unity, needs the Asset Store or mobile reach | Heavier project; free Personal-tier terms and Relay/Vivox limits need *verify* |
| **Unreal 5.8 (C++ + Blueprints)** | High-end visuals or large worlds, or the user already knows Unreal | Heaviest build and review; Blueprint files are binary; weak fit with "simple and goofy" |

Default recommendation for "friendslop / party / low-poly / $0": **Godot**. Say why in one line, and accept the user's choice either way.

---

## 2. Godot profile

**Vocabulary for the prompt:** GDScript `.gd` scripts (one per category, e.g. `shop1objs.gd`, `players.gd`, `roomlogic.gd`, `mall1.gd`); scenes `.tscn` (a "prefab" is a scene); signals; autoloads. Seams: `net.gd` (Net), `state.gd` (State), `events.gd` (Events).

**Architecture example to paste:**
```
levels/       one folder per level, each holding its areas (mall1/ -> shops/shop1/ {shop1.tscn, shop1objs.gd, models/})
objects/      items shared across levels: scene + script + models together
characters/   players/ (player.tscn, players.gd, models/), enemies/
ui/           main_menu/, room/, hud/, game_over/, victory/, settings/
network/      net.gd (all multiplayer), roomlogic.gd
shared/       palette, the one shader, state.gd, events.gd
audio/ addons/ tests/ _project/   (docs: vision, style bible, decisions, credits, toolchain)
```

**Tool References block (paste into Part 4):**
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
```
**$0 flags:** voice (needs an addon; fallback above), NAT traversal (free options only; some pairs fail), generative 3D (off).

---

## 3. Unity profile

**Vocabulary for the prompt:** C# `.cs` (one MonoBehaviour per file, file name = class name, e.g. `Shop1Objs.cs`, `Players.cs`, `RoomLogic.cs`, `Mall1.cs`); prefabs `.prefab`; scenes `.unity`; ScriptableObjects for data. Seams: a `NetService` (Net), a `GameState` (State), a static `Events` class (Events).

**Architecture example to paste:**
```
Assets/Game/Levels/       one folder per level, each holding its areas (Mall1/ -> Shops/Shop1/ {Shop1.prefab, Shop1Objs.cs, Models/})
Assets/Game/Objects/      items shared across levels: prefab + script + models together
Assets/Game/Characters/   Players/ (Player.prefab, Players.cs, Models/), Enemies/
Assets/Game/UI/           MainMenu/, Room/, Hud/, GameOver/, Victory/, Settings/
Assets/Game/Network/      NetService.cs (all multiplayer), RoomLogic.cs
Assets/Game/Shared/       palette, the one material/shader, GameState.cs, Events.cs
Assets/Game/Audio/  Assets/Tests/  _project/ (repo root: vision, style bible, decisions, credits, toolchain)
Keep everything under Assets/Game/ so plugins and samples do not mix with the game.
```

**Tool References block (paste into Part 4):**
```
ENGINE: Unity 6.3 LTS (6000.3), URP, C#. (Verify Unity's current free Personal-tier terms against the $0 rule before starting.)

EDITOR CONTROL (install ONE):
- Default: CoplayDev/unity-mcp ("MCP for Unity", v10.3.0 on 2026-10-04; Unity 2021.3 LTS to 6.x; needs Python 3.10+ via uv).
  Package Manager > Add from git URL: https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#<pinned release tag>
  then Window > MCP for Unity > Configure All Detected Clients.
- Alternative: IvanMurzak/Unity-MCP ("AI Game Developer"; editor AND runtime; generates project skills; project path must contain no spaces).
- Do NOT rely on Coplay MCP or Aura (free only during beta / paid).

SKILLS (engine detail only; this prompt's structure rules win):
  npx skills add gamedev-skills/awesome-gamedev-agent-skills      (router + 8 Unity skills pinned to Unity 6.3 LTS)
  Useful: unity-csharp-scripting, unity-input-system, unity-physics, unity-animation, unity-scriptableobjects, unity-navmesh, unity-build-pipeline;
  cross-engine: game-feel, level-design, physics-tuning, performance-optimization, create-game-assets, audio-design, camera-systems, input-systems.
  Note: the catalog has no Unity networking skill.

ASSETS: Blender MCP (ahujasid/blender-mcp, MIT): DISABLE_TELEMETRY=true claude mcp add blender uvx blender-mcp. Free: Kenney, Quaternius, KayKit (CC0), Poly Haven;
  Unity Asset Store free assets (Unity-only license); Fab free items (read each license). Export FBX/glTF at 1 unit = 1 m with applied transforms.

NETWORKING: Netcode for GameObjects 2.13.x (official) or Mirror (MIT), host + clients; direct IP / LAN works at $0. Unity Relay/Lobby need a Unity Cloud project: verify free limits first.
  Reference project: Unity-Technologies/U6-First-Person-Multiplayer (NGO + Relay + Vivox proximity voice, 4 players, pick-up/throw physics objects).
VOICE (only if required): the only fully free path found is OpenVoiceSharp (C#, MIT/BSD: Opus + RNNoise + voice detection) with your own transport and 3D playback.
  Vivox: verify free tier. Photon Voice and Dissonance are paid: do not use. Fallback: Discord + speaking indicator.

TESTS: Unity Test Framework (EditMode/PlayMode, NUnit); batch-mode compile check (verify flags for 6.3); two-build multiplayer test.
RELEASE: unity-build-pipeline skill; itch.io via butler is the $0 path.
```
**$0 flags:** Unity Personal eligibility *verify*; Relay and Vivox limits *verify*; paid voice SDKs.

---

## 4. Unreal profile

**Vocabulary for the prompt:** C++ classes (one class per header/source pair, e.g. `Shop1Objs`, `PlayersCharacter`, `RoomLogic`, `Mall1`) with **Blueprint subclasses only for asset wiring and tuning** (the standard Unreal pattern); levels `.umap`; Epic prefixes (`A`, `U`, `F`, `E`, `BP_`, `SM_`, `M_`). Seams: a Net game-instance subsystem, the `AGameStateBase` subclass (State), a world subsystem holding delegates (Events). Ask the user whether logic is C++ or Blueprint.

**Architecture example to paste:**
```
Source/<Game>/Levels/       one folder per level, each holding its areas (Mall1/ -> Shops/Shop1/)
Source/<Game>/Characters/   Players/, Enemies/            Source/<Game>/Objects/   items shared across levels
Source/<Game>/Network/      Net subsystem (all multiplayer), RoomLogic         Source/<Game>/Shared/  State, Events
Content/Levels, Content/Characters, Content/Objects, Content/UI, Content/Shared, Content/Audio   (mirror the Source category names)
_project/ at repo root (vision, style bible, decisions, credits, toolchain)    Plugins/ for vendored third-party code
```

**Tool References block (paste into Part 4):**
```
ENGINE: Unreal Engine 5.8 (June 2026). C++ base classes + Blueprint subclasses (confirm). (Verify Epic's current royalty/license terms against the $0 rule.)

EDITOR CONTROL (install ONE):
- Default: ChiR24/Unreal_mcp ("unreal-engine-mcp-server"; MIT; UE 5.0 to 5.8; editor plugin serving MCP at http://localhost:3000/mcp; npm + MCP registry).
- Also: Epic's official "Unreal MCP" plugin (ships with 5.8, EXPERIMENTAL; check the 5.8 release notes on whether a source build is needed).
- No-plugin option for UE 5.0-5.6: ATDev UEMCP:  claude mcp add unreal -- uvx uemcp   (uses UE's built-in Python remote execution; treat it as the editor's Python console).
- Avoid: IvanMurzak/Unreal-MCP on its default hosted cloud backend; paid Ludus AI and Fab "Claude Assistant".

SKILLS (engine detail only; this prompt's structure rules win):
  /plugin marketplace add ibrews/ue5-mcp     then   /plugin install ue5-mcp@ibrews-ue5-mcp        (engine-level knowledge for UE 5.7/5.8)
  npx skills add gamedev-skills/awesome-gamedev-agent-skills   (router + 6 Unreal skills pinned to UE 5.8: unreal-blueprints, unreal-cpp-gameplay,
  unreal-enhanced-input, unreal-behavior-trees, unreal-niagara, unreal-packaging; plus cross-engine game-feel, level-design, performance-optimization, create-game-assets).
  Note: the catalog has no Unreal networking or testing skill.

ASSETS: Blender MCP (ahujasid/blender-mcp, MIT): DISABLE_TELEMETRY=true claude mcp add blender uvx blender-mcp. Free: Kenney, Quaternius, KayKit (CC0); Fab free items
  (Standard License; read each asset's license; the full Megascans library is no longer free, a starter pack and rotating free drops remain).
  Keep the style stylized/low-poly; switch Nanite, Lumen and photoreal scans off unless the vision needs them.

NETWORKING: built-in replication with a listen server (host-authoritative is native), Online Subsystem Null for LAN. Epic Online Services for NAT traversal: verify free terms.
VOICE (only if required): EOS Voice (verify) or ODIN by 4Players (verify pricing). Fallback: Discord + speaking indicator.

TESTS: Automation / Functional Tests (headless editor command with -nullrhi; verify flags for 5.8); two-client listen-server test.
RELEASE: unreal-packaging skill (cook and package); itch.io via butler is the $0 path.
```
**$0 flags:** Epic royalty terms *verify*; EOS and ODIN terms *verify*; Blueprint-only projects are hard for a human to review.

---

## 5. Cross-engine block (always appended after the engine block)
```
CUSTOM AGENTS (optional, for large builds): the nine step-specific agents of the game-builder skill (game-director, architect, gameplay-programmer, network-engineer,
tech-artist, level-builder, qa-edge-hunter, performance-profiler, handover-reviewer). General second-opinion agent: voltagent-domains:game-developer
(claude plugin marketplace add VoltAgent/awesome-claude-code-subagents; claude plugin install voltagent-domains).
IDEA SOURCES (read for ideas, do not adopt wholesale): Claude Code Game Studios (a heavy 30-document process ranked last on play quality in its own measurement),
Genex Desktop (web/Three.js only), Scenario (2D only, free tier unclear): none is required.
RESEARCH RULE: research tools once, at the start; verify each version, license and free-tier limit above is still current; pin the result in _project/TOOLCHAIN.md. Do not re-research later.
```

## 6. Web-first alternative
If the user wants a browser-only game with no install: Three.js (3D) or Phaser (2D); skills `threejs-*` / `phaser-*` exist in the same catalog; networking becomes WebRTC with free signaling
(some pairs fail without a paid relay); Genex Desktop is relevant. Keep the same architecture and execution rules, replace the vocabulary.
