# Custom Agent Roster (one per kind of workflow step)

Nine subagents, each owning one kind of step, written to follow this standard. Files are in `assets/agents/` and are copied into a project's
`.claude/agents/` by `scaffold.py` (Claude Code reads project agents from there; `~/.claude/agents/` makes them global).

## When to use agents at all
A single agent following this skill is enough for small games and small tasks. Delegate to a specialist only when **the task is big, the context would
bloat, or you want an independent check** (QA, review). Real-world evidence points the same way: one published measurement found a heavy multi-agent
process ranked last on play quality against a one-page brief. Keep to these nine; do not add layers of managers.

## The roster
| Agent | Workflow phase | Owns | Tools | Typical trigger |
|---|---|---|---|---|
| `game-director` | 1 Intake, 5 Slice | Vision, fun, scope | read-only | "Is this fun? Is this too much?" |
| `architect` | 2, 4, 6, 8 | Folders, seams, naming, `ARCHITECTURE.md` | read, edit, bash | New category; scripts growing; tangled links |
| `gameplay-programmer` | 5, 6 | Mechanics and category scripts | read, edit, bash | Implement a mechanic or item type |
| `network-engineer` | 4, 5, 7 | Rooms, authority, sync, voice transport, G4 | read, edit, bash | Anything multiplayer |
| `tech-artist` | 3, 6 | Style bible, shader, Blender, lineup, credits | read, edit, bash | Before any asset enters the game |
| `level-builder` | 5, 6 | Levels, slots, randomization, navigation | read, edit, bash | New map; random placement; stairs/lifts |
| `qa-edge-hunter` | 7 (+after features) | Gates, adversarial testing, regression tests | read, edit, bash | "Try to break it" |
| `performance-profiler` | 7 | Frame-rate target | read, edit, bash | Below target FPS |
| `handover-reviewer` | 8 | Newcomer test, docs accuracy | read-only + bash | Before delivery |

## How to run them
1. **One agent per file area at a time.** Two agents editing the same folder collide. Parallelize only independent areas (two different malls, or art vs networking).
2. **Hand off through files, not chat.** Decisions go to `_project/DECISIONS.md`, bugs to a list, assets to `CREDITS.md`, structure to `ARCHITECTURE.md`. The next agent reads those.
3. **Every agent reads `_project/TOOLCHAIN.md` first** and uses only the pinned engine, tools and skills (it does not re-research).
4. **Gates decide "done", not the agent's opinion.** `qa-edge-hunter` and `handover-reviewer` re-run them independently.
5. **Order of a typical build:** `game-director` (vision) -> `tech-artist` (style) -> `architect` + `network-engineer` (skeleton) -> `gameplay-programmer` + `level-builder` (slice) -> repeat content loop -> `qa-edge-hunter` + `performance-profiler` -> `handover-reviewer`.

## Companion agents from outside
- `voltagent-domains:game-developer` (VoltAgent/awesome-claude-code-subagents): a general senior game developer for second opinions; it does not know this standard.
- `code-reviewer`, `refactoring-specialist` (same collection): use after big changes; tell them to apply the size caps and header rule.
Install: `claude plugin marketplace add VoltAgent/awesome-claude-code-subagents` then `claude plugin install voltagent-domains`.

## Customizing
Each file is short plain Markdown with front matter (`name`, `description`, `tools`). To tune one, edit its rules; keep the "Read first" and "Done when" lines. Add an engine-specific rule
at the end of the file when the engine needs it (for example, "Unreal: C++ logic, Blueprint for asset wiring").
