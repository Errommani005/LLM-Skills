# Architecture Reference

Read this when laying out folders, adding a new category, or explaining the project to a human reviewer.
The rules (folder by category, one compact script per category, three seams) are in `standard.md` sections 6-7.
This file shows how they look in practice.

## Contents
1. Naming
2. Scene and script conventions (beginner-safe)
3. Worked example: a level that connects its areas
4. Layout per game type
5. How do I add a new...
6. Seams: what belongs where
7. Anti-patterns

## 1. Naming
- Folders and files: `snake_case`, plain English. Scripts named by category: `shop1objs.gd`, `vehicles.gd`, `player.gd`, `net.gd`.
- Scene root node = the folder's name in `PascalCase` (`Shop1`). One script per scene, attached to the root.
- Signals are past tense (`item_broken`, `round_ended`). Functions are verbs (`grab_item`). Variables are nouns.
- Group names are plural lowercase (`shops`, `players`, `enemies`).
- Tunable numbers are `@export` variables at the top of the script so they can be changed in the inspector.

## 2. Scene and script conventions (beginner-safe)
- **Signals go up, calls go down.** A parent may call methods on its children. A child never reaches up to its parent:
  it emits a signal and the parent connects to it. This one rule prevents most spaghetti.
- A script only touches nodes inside its own scene, plus the three autoloads (`Events`, `State`, `Net`).
- Find objects by **group** (`get_tree().get_nodes_in_group("shops")`) or `@export` references set in the editor. Avoid long
  `get_node("../../Shop1/Door")` paths: they break when the scene is rearranged.
- A scene is the equivalent of a "prefab": built once, instanced many times. Variation comes from `@export` values, not copy-pasted scenes.

## 3. Worked example: a level that connects its areas

`levels/mall1/mall1.gd` knows its shops only through a group and a signal. Adding `shop4` means adding a scene and putting it in the group: **no code change**.

```gdscript
# mall1.gd - Level 1: the mall. Connects its shops to the round logic.
# WHAT:     starts the round, counts loot delivered, decides win/lose.
# TALKS TO: every node in group "shops" (listens to item_delivered), State, Events.
# SIBLINGS: shops/shop1/shop1objs.gd, shop2objs.gd ... each defines `signal item_delivered`.
extends Node3D

@export var loot_needed := 5
var delivered := 0

func _ready() -> void:
	for shop in get_tree().get_nodes_in_group("shops"):
		shop.item_delivered.connect(_on_item_delivered)

func _on_item_delivered() -> void:
	delivered += 1
	State.score = delivered
	if delivered >= loot_needed:
		Events.round_ended.emit(true)
```
```gdscript
# shop1objs.gd - Shop 1: shelves, carts and breakable props.
# WHAT:     all objects inside Shop 1 and how they react to hits.
# TALKS TO: mall1.gd (through the item_delivered signal).
# SIBLINGS: shop2objs.gd has the same break logic. Keep in sync by hand.
extends Node3D

signal item_delivered
@export var break_force := 8.0

func _ready() -> void:
	add_to_group("shops")
```

## 4. Layout per game type
Run `scripts/scaffold.py --type <type>` to generate these. All include `_project/`, `shared/`, `ui/`, `audio/`, `addons/`, `tests/`.

| Type | Content folders |
|---|---|
| party-coop | `levels/level1/`, `characters/players/`, `characters/enemies/`, `objects/` (+ `network/`, `ui/room/` if online) |
| platformer | `levels/world1/level1/`, `characters/player/`, `characters/enemies/`, `objects/pickups/`, `objects/hazards/` |
| shooter | `levels/arena1/`, `characters/player/`, `characters/enemies/`, `weapons/`, `objects/` |
| racing | `tracks/track1/`, `vehicles/`, `objects/` |
| puzzle | `puzzles/` (data per level), `board/` (pure rules), `objects/` |
| strategy | `maps/map1/`, `units/`, `buildings/`, `data/` |
| survival | `world/`, `characters/player/`, `characters/enemies/`, `items/`, `crafting/`, `data/`, `saves/` |
| narrative | `story/` (data), `scenes/`, `characters/npcs/` |
| arcade | `levels/level1/`, `characters/player/`, `characters/enemies/`, `objects/` |

Growth rule: a new level is a new folder beside the first (`levels/mall2/`), self-contained. If a prop is used by 2+ levels, move it
to `objects/<prop>/`. If it is only used by one, it stays in that level's folder.

## 5. How do I add a new...
Every repeatable content type gets a short recipe in `ARCHITECTURE.md`. Example:

```
Add a new shop:
1. Copy levels/mall1/shops/shop1/ to shop4/ and rename the files (shop4.tscn, shop4objs.gd).
2. Open shop4.tscn, change the models, keep the root script.
3. Drag shop4.tscn into mall1.tscn. It joins group "shops" by itself.
4. Add its models to _project/lineup.tscn and check they fit the style.
5. Add any new assets to _project/CREDITS.md.
```

## 6. Seams: what belongs where
| Seam | Holds | Never holds |
|---|---|---|
| `Net` | host/join/leave, player list, kick, room codes | gameplay rules |
| `State` | phase, round number, score | logic that changes the phase (the level script does that) |
| `Events` | signals only | variables, functions |

A fourth autoload is a red flag (`check_project.py` fails it). If it is needed, argue for it in `DECISIONS.md` and drop one.

## 7. Anti-patterns (reject on sight)
- A `utils.gd` or `helpers.gd` that grows forever: put the code in the category script that uses it.
- Base classes for objects that only share a few lines: duplicate the lines and add a sibling comment.
- Scripts that reach across the tree with long paths or `get_parent().get_parent()`.
- Magic numbers inside functions: lift them to `@export`.
- A folder named `misc`, `stuff` or `common`.
- Folders organized by file type (`scripts/`, `models/`, `scenes/` at the top): that is exactly what this layout avoids.
