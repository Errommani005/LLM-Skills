# Assets: style, sourcing, Blender, and the lineup gate

Read this when choosing a visual style or adding any model, texture or sound.

## Contents
1. Choosing the style (ask the user; recommend one)
2. The shared look: palette and shader
3. Sourcing order and the license ledger
4. Making custom assets with Blender MCP
5. Blender to Godot (glTF) rules
6. Rigging and animation
7. The lineup gate
8. Audio
9. 2D games

## 1. Choosing the style
Visual style is an expensive-to-reverse choice: ask, with a recommendation. Options and trade-offs are in `standard.md` section 3.

How to recommend:
- 3D and unsure: **low-poly flat/toon**. Free CC0 packs exist in this style, agents can build it from primitives, rigging is light.
- Party game with identical bean-like characters: **simple-geometry blobs**.
- Comedy physics where jank is the joke: **goofy old-school 3D**, only if the user accepts that consistency and polish take longer.
- 2D: **pixel art** (one pixel density everywhere) or **flat vector** (one stroke style everywhere).

Write the decision into `STYLE_BIBLE.md` before any asset is made.

## 2. The shared look: palette and shader
- One **palette image** (`shared/palette.png`, about 16 flat colors, one swatch per cell). Every model's UVs sit on swatches.
  No per-asset textures: this is what makes unrelated assets look like one game.
- One **shader** (`shared/toon.gdshader`, from the templates) on one shared `ShaderMaterial`. Never create a second shader.
- Recoloring a prop = move its UVs to another swatch, never a new material.
- Lighting: one directional light plus soft ambient. No real-time GI, no baked shadows.

The shader template loads without errors in headless Godot; confirm it visually in the lineup scene (headless mode cannot render it).

## 3. Sourcing order and the license ledger
1. Engine primitives (CSG boxes, capsules, spheres) for blockouts and simple props.
2. **CC0 packs** in the style: Kenney (very wide, blocky), Quaternius (many animated characters), KayKit (dungeon kits, characters), Poly Haven (textures/HDRIs).
3. Poly Pizza / Sketchfab filtered to **CC0**.
4. **Blender MCP** custom builds for anything missing.
5. Generative AI services: last resort. They usually break the style (high poly, mismatched textures) and often need paid credits.

Packs in different styles still clash. Choose one pack family as the base (e.g. Kenney) and fill gaps from the same family first.
Re-color incoming assets to the shared palette (step 2) so mixed sources unify.

License ledger rules (`_project/CREDITS.md`, see `standard.md` section 4): every asset logged on entry; CC0 preferred; CC-BY only with
the credit written; anything else rejected. Packs such as Quaternius may not be re-sold or redistributed as a standalone pack: ship them inside a game only.

## 4. Making custom assets with Blender MCP
Blender MCP (`uvx blender-mcp` + the Blender add-on, Connect to Claude) lets the agent run Python in Blender and read the scene.

Workflow per asset:
1. Read `STYLE_BIBLE.md` (poly budget, proportions).
2. Build from primitives: cube, cylinder, sphere, bevel; **no sculpting, no subdivision, no boolean mess**. Chunky silhouettes read best.
3. Check the triangle count against the budget (`len(obj.data.polygons)` after triangulating).
4. UV-map faces onto palette swatches (no texture painting).
5. Add collision meshes named with Godot suffixes (section 5).
6. Export `.glb` into the owning category folder (`levels/mall1/shops/shop1/models/`).
7. Place it in the lineup scene and compare. Reject and redo if it does not fit.

Prompt pattern that works: "Build `shelf_long` from boxes, 1.2 x 0.4 x 2 m, max 300 tris, UV to swatches 3 and 7 of
palette.png, add `shelf_long-col` as a single box, export glb to <path>."

Poly Haven integration in the MCP is for HDRIs and textures; leave it off unless the style bible allows realistic textures.
**Hyper3D/Rodin generation is off by default**: it needs an API key and produces meshes that rarely match a low-poly style.
Set `DISABLE_TELEMETRY=true` when launching the MCP server.

## 5. Blender to Godot (glTF) rules
- Export **.glb** (binary glTF).
- Scale: 1 Blender unit = 1 meter. Apply scale and rotation (Ctrl+A) before export.
- Origin at the base center of the object so it sits on the floor when placed at y = 0.
- Collision: separate simple meshes named `<name>-col` (collider plus visible mesh), `<name>-colonly` (collider only),
  or `<name>-convcolonly` (convex collider only). Never collide on the visual mesh.
- Characters: forward axis -Z in Godot terms; test by dropping the model in a scene and rotating the node, never fix it by guessing.
- Do not embed per-asset materials: material comes from the shared shader.

## 6. Rigging and animation
- Prefer pre-rigged CC0 characters (KayKit, Quaternius, Kenney) and keep their skeleton so their animations work.
- Mixamo animations (free with an Adobe account) retarget onto humanoid rigs: use them inside the game, do not redistribute the raw files.
- Simple-geometry characters (capsule + eyes) do not need a skeleton: animate with `AnimationPlayer` or `Tween` squash/stretch and rotation.
- Fewer animations, well chosen: idle, walk/run, jump/fall, one action, hit/death.

## 7. The lineup gate
`_project/lineup.tscn`: an empty scene with the shared light and one row per category (characters, props, environment).
Every new asset is added and a screenshot saved to `_project/evidence/lineup-<date>.png`. Ask: same palette? same scale? same
level of detail? same edge softness? If any answer is no, fix or reject before the asset is used anywhere.

## 8. Audio
- Sources: Kenney audio packs (CC0), Freesound (check each file's license, prefer CC0), self-made with free tools (e.g. jsfxr-style generators) for blips.
- One bus layout: Master, Music, SFX; a volume slider for each in `ui/settings`.
- Sounds are short and chunky to match the style. Log every file in `CREDITS.md`.
- Never auto-play loud audio at startup; web builds need a click before sound.

## 9. 2D games
Same gate, different tools: choose one pixel scale (e.g. 16 px tiles), one palette, no rotated sprites if pixel art, import with nearest-neighbor
filtering, and use Kenney 2D packs (CC0) as the base. Blender is optional; use any free pixel/vector editor and export PNG/SVG.
Add sprite sheets to the lineup scene exactly like 3D assets.
