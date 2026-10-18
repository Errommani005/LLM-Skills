# Genre Playbook: a different standard per kind of game

Read **only the section for the game's type** (plus the cross-cutting tables). Each section has the same fields:
**Loop** (what the player repeats), **Feel** (what must be true to be fun), **Controls and camera**,
**Structure** (folders and scripts), **Network default**, **Edge cases**, **Scope cap**, **Fun test**.

## Contents
- Cross-cutting: dimension, platform, performance budgets
- Party / co-op (friend games)
- Platformer
- Shooter (top-down, twin-stick, first/third person)
- Racing / vehicles
- Puzzle / board / card
- Strategy / tower defense
- Survival / crafting / open world
- Narrative / visual novel
- Arcade / score attack
- Hybrids and unknown genres

---

## Cross-cutting: dimension, platform, performance

| Choice | Standard |
|---|---|
| **2D** | Pick one pixel scale or one vector style and never mix. Use `CharacterBody2D`, `TileMapLayer`, one `Camera2D`. |
| **3D** | Low-poly flat/toon default (see `assets.md`). One shared material. One directional light. Prefer `CharacterBody3D` over rigid-body players. |
| **PC (Win/Linux/Mac)** | Target 60 FPS on integrated graphics. Provide a settings screen: volume, fullscreen, key rebinding if more than 6 actions. |
| **Web** | Compatibility renderer; no ENet; audio starts after a click; keep the download small; test in a real browser. |
| **Mobile** | Touch controls with big targets, safe-area margins, Compatibility or Mobile renderer, no hover-only UI. |

Performance habits for every genre (cheap, no profiler needed until it matters):
pool anything spawned often (bullets, coins), cap rigid bodies and let them sleep, use `MultiMeshInstance3D` for
hundreds of identical props, keep one light and no real-time global illumination, and watch Godot's Monitors
panel for the frame time once per phase. Optimize only what the Monitors panel shows to be slow.

Universal feel rules: every action gets feedback within one frame (sound, flash, or motion); every menu has a
Back; pause works everywhere; restart takes under 3 seconds; no text wall before the first action.

---

## Party / co-op (friend games)

- **Loop:** a short objective each round that players do together, with physical or social chaos.
- **Feel:** shared funny moments; failure is amusing, not frustrating. Rounds of 3-5 minutes, sessions 10-20.
- **Controls and camera:** third person, one fixed distance; move, jump, one interact/grab, one throw. 4-5 actions max.
- **Structure:** `levels/<level>/` with sub-folders per area, `characters/players/`, `network/net.gd`, `ui/room/`.
  One object script per area (`shop1objs.gd`); the level script (`mall1.gd`) connects to each area through
  signals and a group, not hard paths.
- **Network default:** online, host-authoritative, 2-4 players (`networking.md`). Movement client-authoritative, items and round state host-authoritative.
- **Edge cases:** two grab one item; carrier disconnects (drop and reset the item); item falls out of the
  world (respawn at its spawn point); player stuck (stuck-button that teleports to spawn after a few seconds);
  player is the only one left; late joiners (room closed once playing); a second round has no leftovers;
  physics objects pile up (cap and despawn); friendly fire off; player count changes mid-round (scale the target).
- **Scope cap:** one level, one objective type, 3 object types, 1-2 enemies. Add content only after the vertical slice is fun.
- **Fun test:** with two real windows, a round ends with someone laughing or arguing in good humor.

## Platformer

- **Loop:** move, jump, avoid hazards, reach the goal, repeat with new arrangements.
- **Feel:** forgiving jumps. **Coyote time** (~0.1 s to jump after leaving a ledge), **jump buffer** (~0.1 s
  early press still counts), **variable jump height** (release early = short jump), and acceleration, not instant speed.
- **Controls and camera:** left/right, jump (one action button optional). Side-scroll camera with a small dead-zone and
  look-ahead; 3D platformers use a follow camera with collision pull-in.
- **Structure:** `levels/world1/level1/`, `characters/player/`, `objects/pickups/`, `objects/hazards/`. Player script
  owns movement; hazards and pickups each get one compact script in their folder.
- **Network default:** none or local. Online platformers need rollback-quality sync: avoid unless asked.
- **Edge cases:** falling out of the world (kill plane then checkpoint); moving platforms carrying the player; one-way
  platforms; corner clipping; jumping on the frame of landing; pause during a jump; checkpoint after death restores
  collected items consistently; very fast fall speed tunnels through floors (cap fall speed).
- **Scope cap:** 3-5 short levels (1-2 min each), 2 hazards, 1-2 enemy types.
- **Fun test:** the first jump feels good in 10 seconds, before any level exists (build a test room first).

## Shooter (top-down, twin-stick, first or third person)

- **Loop:** see enemy, aim, shoot, get feedback, manage ammo/position, repeat in waves.
- **Feel:** punchy hits: muzzle flash, hit flash, small hit-stop, impact sound, short screen shake. Enemies telegraph before attacking.
- **Controls and camera:** top-down/twin-stick: move + aim + shoot. FPS/TPS: mouse look with a sensitivity and FOV setting;
  Esc releases the mouse and pauses; capture it again on click.
- **Structure:** `levels/arena1/`, `characters/player/`, `characters/enemies/`, `weapons/` (bullet scene + `weapons.gd`).
- **Network default:** none, local, or online co-op vs. AI. Hitscan resolved on the host.
- **Edge cases:** enemy cap and pooling; spawn not inside walls or on the player; ammo at zero; reload interrupted by
  weapon swap; bullets tunneling through thin walls (use ray casts for fast bullets); aim at the exact camera
  center; dead enemies still colliding; player dies during pause menu; friendly fire off.
- **Scope cap:** 1 arena, 2 weapons, 3 enemy types, 5-10 wave definitions in a data table.
- **Fun test:** shooting at nothing already feels good; one enemy fight is fun with only 1 weapon.

## Racing and vehicles

- **Loop:** accelerate, steer, take racing lines, finish laps before others or the clock.
- **Feel:** **arcade, not simulation.** Players forgive almost anything except a car that flips or sticks. Prefer a simple
  sphere/body controller with fake grip over a full wheel simulation; use `VehicleBody3D` only if it can be tuned in one sitting.
- **Controls and camera:** accelerate, brake/reverse, steer (+ one drift or boost button). Chase camera with smoothing.
- **Structure:** `tracks/track1/` (scene, `track1.gd` with checkpoints), `vehicles/` (one `vehicles.gd` for all cars), `objects/`.
- **Network default:** online, each player drives their own car (client-authoritative); the host owns lap counting and results.
- **Edge cases:** car upside-down or stuck (reset button to the last checkpoint); cutting the track (checkpoints must be
  passed in order); wrong-way driving; falling off the map; start countdown lock; tying finish times; player leaves
  mid-race (remove from standings); a lap counter that counts the start line twice.
- **Scope cap:** 1 track, 1-3 cars with the same controller and different numbers, optional AI via a path follower.
- **Fun test:** driving an empty track for 60 seconds is already fun.

## Puzzle, board and card games

- **Loop:** read the state, decide, act, see a clear consequence, solve or lose.
- **Feel:** clarity above all. The rules fit in one sentence. Every move has instant visual feedback. **Undo** always.
- **Controls and camera:** mouse or touch pick-and-place; fixed camera; big targets.
- **Structure:** `board/` holds **pure rules with no visuals** (state in, new state out); `puzzles/` holds one data file
  per level; `ui/` and a thin scene draw the state. This split makes the game testable and the netcode trivial.
- **Network default:** none, or online turn-based: send **moves only** and validate on the host; no per-frame sync.
- **Edge cases:** input during animations (lock input until done); illegal moves (reject, no crash); detect win/lose/stalemate
  exactly once; undo past the start; restarts leave no state; random seeds recorded so a level can be replayed; very fast clicking.
- **Scope cap:** 10-20 hand-checked levels, 3-4 mechanics introduced one at a time.
- **Fun test:** the first puzzle can be solved without reading instructions.
- **Tests:** write GUT tests for `board/` rules: this is where bugs hide and where tests are cheap.

## Strategy and tower defense

- **Loop:** gather or earn resources, spend them on units/towers, watch the outcome, adapt.
- **Feel:** decisions matter and are readable: show ranges, costs, and what the enemy will do next.
- **Controls and camera:** mouse select/place; pan and zoom camera; pause and speed-up buttons.
- **Structure:** all numbers in `data/` tables (costs, damage, waves), not buried in scripts; `units/`, `buildings/`, `maps/map1/`.
  Use the engine's `NavigationAgent` for pathing.
- **Network default:** none; online co-op only with small unit counts and host-authoritative snapshots. Lockstep RTS is out of scope.
- **Edge cases:** placing a tower that blocks every path (validate and refuse); selling or upgrading mid-wave; unit cap;
  wave timer when paused; units stuck on corners; negative resources; 0-enemy waves; speed-up breaking timers (use delta-based time).
- **Scope cap:** 1 map, 4 tower/unit types, 10 waves.
- **Fun test:** wave 3 forces a real choice.

## Survival, crafting and open world

- **Loop:** gather, craft, survive needs, expand, explore.
- **Feel:** a steady stream of small rewards; needs (hunger, cold) create pressure but never feel unfair.
- **Controls and camera:** first or third person; hotbar numbers; one inventory screen.
- **Structure:** `items/` and `crafting/` as data resources, `world/` for generation, `saves/` for persistence, `data/` tables.
- **Network default:** none, or online co-op where the host owns the world and the save.
- **Warning: this is the largest scope.** Do a vertical slice with **one biome, one crafting chain, one threat**. Ask the user before
  accepting more. The scope cap is a hard rule here.
- **Edge cases:** **save system from day one** with a version number (old saves must not crash new builds); inventory full (drop on the
  ground, never delete); stack limits; crafting with exact ingredients; save during death; world chunks unloading under the player;
  day/night cost; items duplicating via drop-and-pickup spam.
- **Fun test:** in 10 minutes the player has gathered, crafted one tool, and used it to get something new.

## Narrative and visual novel

- **Loop:** read, choose, see consequences, reach endings.
- **Feel:** effortless reading: click to advance, skip seen text, backlog, save anywhere.
- **Controls and camera:** one advance input; no camera.
- **Structure:** `story/` holds the script as **data** (JSON or Resource files), never as code; `scenes/` for backgrounds and
  character poses; one small script plays the data. Do not write a custom scripting language.
- **Network default:** none.
- **Edge cases:** choice flags that become inconsistent; skipping past a choice; loading a save mid-line; missing character/background
  reference (show a clear placeholder and a log); very long lines; text speed zero; rollback.
- **Scope cap:** one story, 2-3 endings, under 30 minutes.
- **Fun test:** a tester reaches an ending without asking how to progress.

## Arcade and score attack

- **Loop:** play a short run, die, see the score, instantly try again.
- **Feel:** **instant restart** (under one second), a difficulty curve that ramps smoothly, readable risk and reward.
- **Controls and camera:** 1-3 actions; fixed or simple camera.
- **Structure:** `levels/level1/` (or a single arena), `characters/`, `objects/`; `State` holds score; a local high-score file.
- **Network default:** none; optional shared-seed "daily run" without servers (same seed, compare scores by hand).
- **Edge cases:** pause exploits; score overflow; high-score save failing (keep playing); restart mid-animation; difficulty at extremes.
- **Scope cap:** one mode, 3-5 obstacle/enemy types, one scoring rule.
- **Fun test:** testers say "one more try" without prompting.

## Hybrids and unknown genres

1. Find the closest section and take its **Feel**, **Edge cases** and **Scope cap**.
2. Name the one **fun source** in `GAME_VISION.md` and protect it: cut anything that does not serve it.
3. If two genres collide (e.g. racing + co-op), the stricter scope cap wins.
4. If nothing fits, treat it as **arcade** until a prototype proves the loop is fun, then specialize.
5. Log the hybrid decision in `DECISIONS.md`.
