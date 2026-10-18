# Toolchain: index and verdict rules

Dated **October 2026**. The detailed, per-engine, per-step lists are in four files. Read the one for the chosen engine at Phase 2, then write the result into `_project/TOOLCHAIN.md`.
Agents read `TOOLCHAIN.md` afterwards, not these files.

| File | Contents |
|---|---|
| `tools-godot.md` | Godot 4.7.x: editor MCPs (Coding-Solo, godot-ai, runtime and file options), skills per phase, TwoVoip voice, GUT, release |
| `tools-unity.md` | Unity 6.3 LTS: Unity MCPs (CoplayDev, IvanMurzak), skills, NGO / Mirror / Relay / Vivox, OpenVoiceSharp, Test Framework |
| `tools-unreal.md` | Unreal 5.8: Unreal MCPs (ChiR24, Epic's official, ATDev, GenOrca), `ue5-mcp` skill, Blueprint-or-C++, replication / EOS, Automation |
| `tools-general.md` | Blender MCP, free asset sources and licenses, awesome-gamedev-agent-skills catalog, agent lists, idea sources, rejected tools |
| `engines.md` | Engine choice and how the standard maps onto each engine |
| `agents.md` | The nine custom agents, one per kind of workflow step |

## Vetting test (every tool must pass all four)
1. Maintained recently and widely used. 2. Free for our use and license-compatible. 3. Works with the pinned engine version. 4. Removes more work than it adds.

## Rules for adopting tools
- **One editor-control MCP per engine** (two editors' servers conflict). Add at most one runtime/inspection tool beside it.
- **Pin versions** (engine, MCP tag, addon release). Never `#main` or `latest` for something the game depends on.
- **Skills never override this standard's structure rules**; they supply engine API detail only.
- Third-party services (relay, voice, VPN) need their **free-tier limits recorded** in `TOOLCHAIN.md`; anything paid is rejected.
- Anything marked **verify** in the tools files must be checked against current official docs before it is relied on.
- Re-check dates: versions and stars drift within months.

## Engine choice
See `engines.md` section 1. Default Godot 4 for simple, low-poly, friends, $0 projects.
