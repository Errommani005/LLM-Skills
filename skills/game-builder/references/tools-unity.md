# Unity Toolchain (verified October 2026)

Read at Phase 2 (Toolchain) for any Unity project. Facts marked **verify** were not confirmed against current official terms: check them before relying on them.

Pin: **Unity 6.3 LTS (6000.3)**, the baseline the companion skills are written against. Language: C#. Render pipeline: URP (simplest for low-poly styles).
Unity's own license and any revenue threshold for the free Personal tier: **verify** current terms against the $0 rule before starting.

## Contents
1. Editor control (MCP)
2. Knowledge skills per workflow phase
3. Assets
4. Networking and voice
5. Testing and gates
6. Build and release
7. Verdict summary

---

## 1. Editor control (MCP)

| Server | What it does | License / cost | Notes |
|---|---|---|---|
| **CoplayDev/unity-mcp ("MCP for Unity")** (default) | Manage assets, scenes, scripts, run tests, automate editor tasks | Open source, free to use. **v10.3.0 (2026-10-04)**; Unity 2021.3 LTS through 6.x; needs Python 3.10+ via `uv` | Install in Package Manager from the git URL below (pin a release tag, not `#main`). Window > MCP for Unity > Configure All Detected Clients. HTTP server on localhost:8080. Multiple editors supported |
| **IvanMurzak/Unity-MCP ("AI Game Developer")** | Editor **and runtime**: create GameObjects, manage assets, write scripts, screenshots, run tests; any C# method becomes a tool with one attribute | Free; 14 client configurators; about 3.1k stars on the MCP registry | **Project path must not contain spaces.** Local server binary auto-downloaded by the plugin. Generates AI skills for your project (`Window > AI Game Developer > Auto-generate skills`, or `npx unity-mcp-cli setup-skills claude-code ./MyUnityProject`) |
| Coplay MCP (coplay.dev, 86 tools) | Large toolset incl. generation | Free **while in beta**, tied to a Coplay subscription | **Not reliably $0.** Skip |
| Aura (premium assistant by the same sponsor) | Paid | Paid | Skip |

Install (default), Unity Package Manager > Add from git URL:
```
https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#v10.3.0      (pin the tag you verified)
# or: openupm add com.coplaydev.unity-mcp
```
Run **one** Unity MCP at a time. Never let the agent make big code changes without version control: commit before every session.

## 2. Knowledge skills per workflow phase

`gamedev-skills/awesome-gamedev-agent-skills` has 8 Unity skills pinned to Unity 6.3 LTS:
`unity-csharp-scripting`, `unity-input-system`, `unity-physics`, `unity-animation`, `unity-scriptableobjects`, `unity-tilemap-2d`, `unity-navmesh`, `unity-build-pipeline`.
```
npx skills add gamedev-skills/awesome-gamedev-agent-skills
claude plugin install router@awesome-gamedev-agent-skills
claude plugin install unity@awesome-gamedev-agent-skills
```
| Workflow phase | Unity skills | Cross-engine skills |
|---|---|---|
| 3 Style | (URP shader graph by hand) | `create-game-assets`, `shader-programming` |
| 4 Skeleton | `unity-csharp-scripting`, `unity-input-system`, `unity-scriptableobjects` | `input-systems`, `game-ui-ux` |
| 5 Vertical slice | `unity-physics`, `unity-animation`, `unity-navmesh` (if AI) | `game-feel`, `camera-systems`, `level-design`, `prototype-fast`, genre skill |
| 6 Content | `unity-scriptableobjects`, `unity-tilemap-2d` (2D) | `save-systems`, `game-ai`, `procedural-gen`, `audio-design` |
| 7 Hardening | (Test Framework, see section 5) | `physics-tuning`, `performance-optimization` |
| 8 Release | `unity-build-pipeline` | `itch-publish` / `steam-publish` |

**Gap:** the catalog has **no Unity networking skill** (only Godot and Roblox have one). For networking read the official sample in section 4 and Unity's NGO docs.

## 3. Assets
- Unity Asset Store free assets: licensed for use inside Unity projects only; you cannot extract them from a compiled game. Log each in `CREDITS.md`.
- Fab also lists Unity-compatible content (see `tools-general.md`; read each license).
- CC0 packs (Kenney, Quaternius, KayKit) import as `.fbx`/`.glb` (glTF needs a package such as glTFast: **verify** current recommendation).
- Style enforcement in Unity: one URP material (or Shader Graph toon shader) with a palette texture; lineup scene `Assets/Game/_Lineup.unity`.
- Blender MCP as in `tools-general.md`; export FBX or glTF with 1 unit = 1 m and applied transforms.

## 4. Networking and voice

| Option | Cost | Notes |
|---|---|---|
| **Netcode for GameObjects (NGO)** | Free package; **2.13.2** for Unity 6000.3 | Official, MonoBehaviour-based. Host/client with Unity Transport works with direct IP or LAN at $0 |
| Unity Multiplayer Services (Relay, Lobby, Sessions) | **Verify free-tier limits** | Solves NAT with relay; requires a linked Unity Cloud project and Unity 6 |
| **Mirror** (v96.x) | MIT, fully free, self-hosted | Mature; many tutorials; no cloud |
| FishNet (4.7.x) | Free, **custom source-available license: read it** before adopting | Strong features; license differs from MIT |
| Netcode for Entities | Free | DOTS-only; too heavy for this standard |
| Nakama | Open-source backend | Backend, not transform netcode; needs hosting |

**Closest official reference for a friends-party game:** `Unity-Technologies/U6-First-Person-Multiplayer`: Unity 6000.3.5+, NGO + Relay + **Vivox proximity voice**, up to 4 players, server-authoritative, players pick up and throw physics objects. Unity Companion License. It needs a Unity Cloud project with Relay and Vivox enabled: **verify** the free tier for both. Read its `LobbyController.cs`, `RelayManager.cs`, `ProximityVoice.cs`.

**Voice at $0:**
- Vivox via Unity Gaming Services: check free tier (**verify**).
- Photon Voice and Dissonance are **paid**: skip.
- **OpenVoiceSharp** (C#, MIT/BSD): Opus + RNNoise + WebRTC voice-activity detection, engine-agnostic; you provide transport (through NGO RPCs) and 3D playback. The only fully free path found.
- A community FMOD-based proximity voice project for NGO exists: quality unverified.
- Fallback: Discord plus an in-game speaking indicator.

Apply the same authority rules as `networking.md` (host decides, clients request); NGO maps them to `ServerRpc`/`ClientRpc` and `NetworkVariable`s.

## 5. Testing and gates
- **G1 Boots:** compile in batch mode, `Unity -batchmode -quit -projectPath <path> -logFile -` and scan the log for `error CS`. (**Verify** flags for your version.)
- **G3 Logic tests:** Unity Test Framework (built in, NUnit): EditMode tests for rules, PlayMode for behavior; CLI `-runTests -testPlatform EditMode`. Both MCP servers above can run tests from the agent.
- **G2 Screenshot:** the MCP's screenshot tool, or `ScreenCapture.CaptureScreenshot` in a PlayMode test.
- **G4 Multiplayer:** two builds (or Multiplayer Play Mode, Unity's multi-instance editor feature, **verify** availability in your version) on one machine; script the same scenarios as `net_test.sh` (full room, late joiner, host leaves, duplicate names).
- GameCI (open-source GitHub Actions for Unity) is the common free CI route: **verify** the current Unity license activation requirements before relying on it.

## 6. Build and release
`unity-build-pipeline` skill: build/player/quality settings, code stripping, Addressables. itch.io via `butler` is the $0 path.

## 7. Verdict summary
**Adopt:** CoplayDev/unity-mcp (or IvanMurzak/Unity-MCP), awesome-gamedev-agent-skills (unity + router), NGO or Mirror, Unity Test Framework, OpenVoiceSharp for $0 voice.
**Use with care:** Relay/Vivox (verify limits), FishNet (license), glTFast, GameCI.
**Reject:** Coplay MCP/Aura (not reliably $0), Photon Voice, Dissonance.
