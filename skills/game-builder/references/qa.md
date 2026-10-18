# QA: the five gates, test setup, and edge-case method

"Bug-free" is not something to promise; it is something to demonstrate. A feature is done only when the gates pass.

## Contents
1. The gates and how to run them
2. Evidence: seeing the game
3. Tests with GUT
4. Edge-case method
5. Performance pass
6. Release checklist

## 1. The gates
| Gate | Command / action | Pass means |
|---|---|---|
| G1 Boots | `scripts/gate_boot.sh <project>` | Headless start, no `SCRIPT ERROR`, parse error or load failure |
| G2 Runs and is seen | Godot MCP `run_project`, then capture a screenshot | The key screen exists on screen and looks right; image saved in `_project/evidence/` |
| G3 Logic tests | GUT headless (section 3) | Rules with numbers or state have passing tests |
| G4 Multiplayer | `scripts/net_test.sh <project>` plus two real windows by hand | Scripted edge cases pass and a real round can be played |
| G5 Edge cases | The checklist in `standard.md` section 11 + the genre list in `genres.md` | Each item ticked or logged in `DECISIONS.md` |

Also run `scripts/check_project.py <project>` before every handover: it enforces headers, size caps, the autoload cap, documented
folders and the credits ledger. Errors must be fixed; warnings must be fixed or justified.

If Godot is not on PATH, set `GODOT=/path/to/godot` for the scripts.

## 2. Evidence: seeing the game
A parse check is not a run. A passing test does not prove a menu is on screen. For anything the player sees:
launch the game with a display, reach the screen, save an image. A one-line capture you can call from a debug key or a test scene:

```gdscript
get_viewport().get_texture().get_image().save_png("res://_project/evidence/main_menu.png")
```
Headless mode has no renderer, so it cannot capture images; use it for G1, G3, G4 only. Look at the screenshot: check that text is readable,
nothing is off-screen, colors match the palette, and the HUD does not cover the action.

## 3. Tests with GUT
GUT is the test runner for GDScript-only projects. Pin a release that matches the Godot version, vendor it in `addons/gut/`, enable it
in Project Settings, then:

```
godot --headless -s addons/gut/gut_cmdln.gd -gdir=res://tests -gexit
```
Write tests for **logic with numbers or state**: scoring, inventory stacking, puzzle rules, wave tables, room codes. Do not unit-test visuals.
```gdscript
# test_score.gd - rules for scoring.
extends GutTest

func test_delivering_five_items_wins() -> void:
	State.reset()
	for i in 5: State.score += 1
	assert_eq(State.score, 5)
```
Optional later: a mutation tester (gdmutant) shows whether tests would actually catch a bug.

Known quirk: if GUT reports class-resolution parse errors on a fresh CI checkout, run `godot --headless --import` once before the tests.

## 4. Edge-case method
For each mechanic, answer in writing (in `DECISIONS.md` or a comment):
1. What if it happens **twice at once**?
2. What if it happens **at the worst moment** (round ending, scene changing, paused, disconnecting)?
3. What if the player does it **too fast, too slow, never, or forever**?
4. What if the thing involved **is gone** (destroyed, left the room, out of the world)?
5. What if a **second playthrough** starts from this state?

Then pick: prevent, handle, or accept (and say why). Test the "handle" ones.

## 5. Performance pass
Once per phase: run the game and watch the Monitors panel (frame time, draw calls, physics objects). Targets come from `GAME_VISION.md`
(default 60 FPS on integrated graphics). Fix the slowest thing first and re-measure; common wins: pooling, fewer lights, `MultiMesh`, sleeping rigid bodies.

## 6. Release checklist
- [ ] All gates pass on a fresh checkout.
- [ ] `check_project.py` has no errors and no unexplained warnings.
- [ ] `CREDITS.md` covers every external asset.
- [ ] `export_presets.cfg` committed; builds made for each target platform and launched once.
- [ ] A friend who never saw the game plays a full round without help (30/60-second tests pass).
- [ ] `README.md` explains how to run, how to play, and where things are.
- [ ] Version string (`Net.GAME_VERSION`) bumped for networked games.
