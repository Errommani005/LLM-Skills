# The Standard (your original brief, cleaned up)

> Written with Godot vocabulary. For Unity or Unreal read `engines.md` beside it: it maps every term, folder layout, seam and gate.

This is the rule set every game follows. It is your original instructions with contradictions
resolved, vague phrases made checkable, and an example under each rule.

## Contents
1. What changed and why
2. Vision and fun
3. Visual style
4. Assets and sourcing
5. Tool research
6. Architecture (folders)
7. Code organization (files)
8. Code style (simplicity)
9. Networking and backend
10. Budget
11. Edge cases
12. Quality gates ("bug-free")
13. Decisions and questions
14. Definition of done
15. Human handover

---

## 1. What changed and why

| Original wording | Problem | Standard rule |
|---|---|---|
| "Separate everything into folders" + "don't make it too modular" | These pull opposite ways | **Folders by category, one compact script per category, abstraction only at three named seams** (§7) |
| ".cs files", "prefabs" | Unity words in a Godot project | GDScript `.gd` files; a prefab is a scene `.tscn` |
| "Ask me, or come up with an answer" | No rule for which | **Ask only about expensive-to-reverse choices; decide the rest and log it** (§13) |
| "Bug-free" | Can't be instructed, only verified | **Five gates** that must pass before "done" (§12) |
| "Fewest instructions that do the most work" | Not measurable | Priority order + size caps (§8) |
| "No visual deviation" | No test for it | **Lineup scene gate** (§3) |
| "Free assets as much as possible" | No license rule | **CC0 first, ledger for everything else** (§4) |
| "Research tools online" | Agents wander the web every session | **Research once, pin in `TOOLCHAIN.md`** (§5) |
| "Peer to peer" | Means different things | Defined per case in `networking.md` |
| "Make the game fun" | Not actionable | **30-second / 60-second rules** (§2) |

---

## 2. Vision and fun

**Rule.** Before any code, `_project/GAME_VISION.md` exists and is filled in. The agent never guesses the
game. If a field is missing, it is either asked (if expensive) or decided and logged (if cheap).

**Rule.** Two playability tests every game must pass:
- **30-second rule:** a new player can state the goal after 30 seconds without reading text.
- **60-second rule:** the first moment of fun (a hit, a catch, a win, a laugh) happens within 60 seconds.

**Rule.** Rounds, not marathons, unless the genre demands otherwise. Target session length is written in the vision doc.

**Example: `GAME_VISION.md` (filled in)**
```
Pitch:        Four friends rob a haunted mall before the guard ghost wakes up.
Type:         party-coop
Players:      2-4, online rooms (host-authoritative)
Camera:       third person, fixed distance
Controls:     WASD move, Space jump, E grab, hold LMB throw
Goal:         Carry 5 loot items to the van before the timer ends.
Fail:         Timer hits zero, or all players are caught.
Session:      8-12 minutes, 3 rounds
Fun source:   Physics chaos while carrying awkward loot together.
Style:        low-poly-flat (see STYLE_BIBLE.md)
Platform:     Windows/Linux PC builds, 60 FPS on integrated graphics
Out of scope: voice chat, progression, skins
```

---

## 3. Visual style

**Rule.** One style, written in `STYLE_BIBLE.md`, enforced by a shared shader and one palette. Nothing is
added that does not fit.

**Style options** (pick one per game; default is the first):

| Style | Best for | Agent-friendliness | Risk |
|---|---|---|---|
| **Low-poly, flat or toon shaded** (default) | Almost everything 3D | High: primitives in Blender, free CC0 packs match | Needs one shared material |
| Simple-geometry blobs (Fall Guys / Among Us 3D) | Party games, few characters | High: capsules and spheres, minimal rigging | Looks bland without good colors and sound |
| Goofy old-school 3D (Goat Simulator, Who's Your Daddy) | Comedy physics games | Low: charm depends on janky physics and uneven assets | Hard to keep bug-free and consistent |
| 2D pixel art | Platformers, puzzle, RPG | Medium: needs consistent pixel scale | Mixed pixel densities break the look |
| 2D flat vector | Puzzle, casual, UI-heavy | High | Style drift between assets |

**The lineup gate.** Every new asset is placed in `_project/lineup.tscn` next to existing assets, under the
shared shader and palette. If it looks like it came from a different game, it is rejected or re-skinned.

**Example: `STYLE_BIBLE.md`**
```
Style:        low-poly-flat
Palette:      shared/palette.png (16 colors, see swatches below)
Shader:       shared/toon.gdshader (2 light bands, thin rim light, NO outlines)
Poly budget:  character <= 800 tris, prop <= 300 tris, building <= 2000 tris
Proportions:  chunky; head = 1/3 of character height
Lighting:     one sun, soft ambient, no baked shadows
Forbidden:    realistic textures, normal maps, photoreal HDRIs, gradients on models
```

---

## 4. Assets and sourcing

**Rule: sourcing order.** Stop at the first option that works.
1. Engine primitives (CSG boxes, capsules, spheres) for blockouts and simple props.
2. **CC0 packs** in the target style: Kenney, Quaternius, KayKit (all CC0), Poly Haven for textures and HDRIs (CC0).
3. Poly Pizza / Sketchfab filtered to CC0.
4. **Blender MCP** for anything custom, built from primitives to match the style bible.
5. Generative AI services last, only if they pass the style gate and the $0 rule (see `toolchain.md`).

**Rule: license ledger.** Every external asset gets a row in `_project/CREDITS.md` the moment it enters the repo.
CC0 needs no credit but is still logged. CC-BY is allowed only if its credit line is written. Anything else is rejected.
Some packs forbid reselling or redistributing the raw pack (Quaternius, for one): ship assets inside a game, never as a standalone bundle.

**Rule: Blender to Godot pipeline.** Export `.glb`.
- 1 Blender unit = 1 meter, forward axis as Godot expects, transforms applied.
- Origin at the base center of the object.
- Collision shapes are separate simple meshes named with Godot import suffixes (`-col`, `-colonly`, `-convcolonly`), never the visual mesh.
- One shared material or one palette texture; no per-asset materials.

**Example: `CREDITS.md`**
```
| Asset                 | Source        | License | Author      | Used in               |
|-----------------------|---------------|---------|-------------|-----------------------|
| Dungeon wall pack     | kenney.nl     | CC0     | Kenney      | levels/mall1/         |
| Adventurer character  | kaykit        | CC0     | Kay Lousberg| characters/players/   |
| shelf_long.glb        | made in Blender (MCP) | own | agent  | levels/mall1/shops/shop1/ |
```

---

## 5. Tool research

**Rule.** Research happens **once**, at project start (start from `toolchain.md`, which indexes the per-engine tool lists), and the result is pinned in `_project/TOOLCHAIN.md`:
versions, install commands, license, and a one-line "why". Agents read `TOOLCHAIN.md`; they do not re-research.

**Vetting test** (a tool must pass all):
1. Maintained recently and widely used.
2. Free for our use and license-compatible.
3. Works with the pinned engine version.
4. Removes more work than it adds (the simplicity rule applies to tools too).

Heavy "AI studio" frameworks fail test 4 for this project type: one published measurement found a 30-document
process ranked last on play quality against a one-page brief. Mine them for ideas; do not adopt them wholesale.

**Example: `TOOLCHAIN.md`**
```
Engine:       Godot 4.7.1 stable (pinned; do not upgrade mid-project)
Language:     GDScript
Godot MCP:    claude mcp add godot -- npx @coding-solo/godot-mcp   (MIT)
Blender MCP:  claude mcp add blender uvx blender-mcp   (MIT; set DISABLE_TELEMETRY=true)
Tests:        GUT 9.x (matches Godot 4.x), run headless
Assets:       Kenney, Quaternius, KayKit (CC0)
Rejected:     Hyper3D generation (style drift, needs API key), Tailscale GDExtension (Linux-only, early)
```

---

## 6. Architecture (folders)

**Rule.** The folder tree is the table of contents of the game. A person who has never opened Godot must be
able to find anything by guessing the category. Each category folder is **self-contained**: its scene,
script, and models sit together, so one folder answers one question.

**Example: default layout**
```
res://
  _project/            GAME_VISION, STYLE_BIBLE, DECISIONS, CREDITS, TOOLCHAIN, ARCHITECTURE, lineup.tscn
  levels/
    mall1/
      mall1.tscn  mall1.gd            the level itself and how its shops connect
      shops/
        shop1/  shop1.tscn  shop1objs.gd  models/
        shop2/  shop2.tscn  shop2objs.gd  models/
  characters/
    players/    player.tscn  player.gd  models/
    enemies/    guard.tscn   guard.gd   models/
  vehicles/     van.tscn  vehicles.gd  models/
  objects/      props shared by several levels
  ui/
    main_menu/  room/  hud/  game_over/  victory/  settings/     each: .tscn + .gd
  network/      net.gd  room.gd
  shared/       palette.png  toon.gdshader  state.gd  events.gd
  audio/        music/  sfx/
  addons/       pinned, vendored third-party code
  tests/
```
Single-player games drop `network/` and `room/`. Other game types adapt the tree: see `architecture.md`.

**Rule.** `ARCHITECTURE.md` always has (a) one line per folder and (b) a "where do I find X" table.

**Example: where-do-I-find table**
```
| I want to change...            | Open                                  |
|--------------------------------|---------------------------------------|
| how a player moves             | characters/players/player.gd          |
| what happens in shop 1         | levels/mall1/shops/shop1/shop1objs.gd |
| room codes / joining           | network/net.gd                        |
| the lobby screen               | ui/room/room.gd                       |
| the look of everything         | shared/toon.gdshader, shared/palette.png |
```

---

## 7. Code organization (files)

**Rule.** One compact script per trackable category of objects, containing everything about it
(behavior and physics). `shop1objs.gd` holds shop 1's objects; `vehicles.gd` holds all vehicles.

**Rule: abstraction only at seams.** Exactly three shared seams exist, all in autoloads:
- `net.gd` (**Net**): networking. Changes often and everything touches it.
- `state.gd` (**State**): game phase, scores, player list.
- `events.gd` (**Events**): a signal bus for "something happened" messages between categories.

Everything else is plain, self-contained scripts. **Repetitive logic is allowed to repeat.** Object physics in
`shop1objs.gd` and `shop2objs.gd` may look alike; each carries a comment pointing at its siblings.

**Graduation rule.** If the same fix is applied in three sibling scripts in a row, that logic has proven it
changes often and is linked to others. Promote it to a seam (or a tiny shared helper) and log it in `DECISIONS.md`.

**Mini diagram**
```
mall1.gd ──spawns──▶ shop1objs.gd, shop2objs.gd      (level connects its shops)
   │                         │
   └──── Events (signals) ◀──┘      Net (all multiplayer)      State (phase, score)
```

**Example: header comment on every script**
```gdscript
# shop1objs.gd - Shop 1: shelves, carts and breakable props.
# WHAT:     all physical objects inside Shop 1 and how they react to hits.
# TALKS TO: mall1.gd (spawns this), Events (emits "item_broken").
# SIBLINGS: shop2objs.gd uses the same break logic. Keep in sync by hand.
```

---

## 8. Code style (simplicity)

**Priority order for any feature.** Stop at the first that works:
1. Engine built-ins (nodes, `move_and_slide`, `Tween`, `AnimationPlayer`, `MultiplayerSynchronizer`).
2. A vetted addon pinned in `TOOLCHAIN.md`.
3. Your own short code.

**Size caps (soft; exceeding needs a one-line comment saying why):**
- Function: about 20 lines. File: about 300 lines.
- Max 3 autoloads. Max one level of inheritance.
- No custom base classes, no design-pattern frameworks, no clever one-liners.

**Style:** type function signatures and `@export` variables; infer the rest with `:=`. Names are plain English
(`carry_item`, not `handle_obj_interaction_v2`). Tunable numbers are `@export` variables at the top, never buried.

**Example: bad vs good**
```gdscript
# BAD: many instructions, little work, abstraction nobody asked for
class_name AbstractInteractableFactory extends RefCounted
func create(kind: StringName, ctx: Dictionary) -> Node: ...

# GOOD: shortest thing a careful beginner would write
@export var speed := 6.0
@export var jump_force := 7.5

func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity += get_gravity() * delta
	elif Input.is_action_just_pressed("jump"):
		velocity.y = jump_force
	var dir := Input.get_vector("left", "right", "forward", "back")
	velocity.x = dir.x * speed
	velocity.z = dir.y * speed
	move_and_slide()
```

---

## 9. Networking and backend

**Rule.** Pick the networking mode by the game's needs, not by habit. All networking code lives in `net.gd`.
The decision table, free options, and tested code are in `networking.md`. "Peer to peer" for friend games
means a **host-authoritative listen server**: one friend hosts, others join with a room code, clients send
intents and the host decides truth.

---

## 10. Budget

**Rule.** Total cost is $0. No paid APIs, no hosted servers, no per-seat tools, no asset purchases.
Where a free tier is used, `TOOLCHAIN.md` records the limits so nobody is surprised. If a feature cannot be
done for $0, the agent says so and offers a $0 alternative (e.g. LAN/VPN play instead of a relay).

---

## 11. Edge cases

**Rule.** For every mechanic, the agent writes down what a hostile, clumsy, or unlucky player could do and
handles it. Generic list below; `genres.md` adds per-type lists.

**Always-on checklist**
- Player falls out of the world, clips into a wall, or gets stuck (kill plane + respawn point).
- Input spam, simultaneous inputs, held keys across scene changes, alt-tab mid-action.
- Pause, resize, window lose-focus, controller unplugged.
- Two players do the same thing at the same tick (grab the same item).
- Object destroyed while carried, or leaves the playfield.
- Round ends while something is mid-animation or mid-throw.
- Quit/disconnect at any moment (including host).
- Empty room, full room, join after the game started, duplicate player names, very long names.
- Restart loops: second playthrough must behave like the first (no leftover state).

**Example: logged edge case** (in `DECISIONS.md`)
```
D-012  Two players grab the same crate -> host grants to the first request received,
            second request is ignored (no error). Tested with 2 instances.
```

---

## 12. Quality gates ("bug-free")

You cannot instruct "bug-free". You can require evidence. A feature is not done until all pass:

| Gate | What | How |
|---|---|---|
| **G1 Boots** | Headless start with zero script errors | `scripts/gate_boot.sh` (see `qa.md`) |
| **G2 Runs and is seen** | Game launched, key screen observed, screenshot kept | Godot MCP `run_project`, screenshot in `_project/evidence/` |
| **G3 Logic tests** | Rules with numbers or state have tests | GUT headless |
| **G4 Multiplayer** | Two real instances connect and play a round | `qa.md` two-instance script (if net mode isn't "none") |
| **G5 Edge cases** | The §11 checklist plus the genre list, each ticked or logged | `qa.md` |

A parse check is not a run. A passing test does not prove a menu is on screen.

---

## 13. Decisions and questions

**Rule.** Classify every open question:
- **Expensive to reverse** (core loop, camera, visual style, networking mode, target platform, player count):
  **ask the user.** Offer 2-3 options with one-line trade-offs and a recommendation.
- **Cheap to reverse** (a color, a key binding, a timer length, a prop's placement): **decide, and log it.**

**Example: `DECISIONS.md`**
```
D-004  Round timer = 180 s.   Reason: fits 10-min session with 3 rounds.   Reversible: yes (1 constant).
D-005  Host leaves -> room closes, everyone returns to menu.   Reason: host migration too costly for $0 scope.
```

---

## 14. Definition of done

A game is complete when: the vision doc's goal can be reached and lost from a fresh launch; all five gates
pass; `CREDITS.md` covers every external asset; `ARCHITECTURE.md` matches the folders; a friend who has never
seen the game can play a full round without help.

---

## 15. Human handover

The reviewer may be new to the engine. Deliver: a root `README.md` (what it is, how to run, how to play,
the folder map), `ARCHITECTURE.md`, header comments on every script, and a 5-line "how to add a new X"
recipe for each repeatable content type (new shop, new level, new enemy).
