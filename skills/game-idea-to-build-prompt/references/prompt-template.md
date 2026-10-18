# Build Prompt Template

The final deliverable is ONE Markdown document addressed to the coding agent. Copy the skeleton below into a code block, fill every `{{...}}`, delete guidance lines
(starting with `>`), and keep the section numbers (the checker verifies that every `§N.N` reference points at a real heading).

**What the prompt contains:** the vision, the mechanics, the architecture and execution rules, and tool references for the chosen engine.
**What it deliberately leaves out:** implementation details, algorithms, exact UI layouts, numbers the user did not decide. The building agent decides those and logs them.
State **what** and **which constraints**, never **how**, unless the user specified the how.

## Contents
1. Skeleton
2. Section-by-section guidance
3. Tag convention
4. What to keep verbatim from the user
5. Length and tone

---

## 1. Skeleton

````markdown
# {{GAME TITLE}}: Build Prompt

You are the coding agent that builds this game. Read this whole document first. The user's instructions below are requirements, not suggestions.
Tags: **[ASK]** = stop and ask the user before proceeding, do not guess. **[DEFAULT]** = a proposed default: use it, log it in `DECISIONS.md`, change only with a reason.
Anything not specified here is **yours to decide** (§3.3): decide it, keep it simple, and log it.

---

## PART 1: THE GAME

### 1.1 Pitch
{{One or two sentences: what the game is, who plays, the fantasy.}}

### 1.2 Objective and rules
{{Win condition, lose condition, session length, scoring. One bullet per rule, in the user's own words wherever possible.}}

### 1.3 Core mechanics
> One sub-heading or bold label per mechanic family (movement, items, combat, economy, hazards...). Keep every number and behavior the user gave. Do not invent numbers: if missing, move it to §3.

### 1.4 Content
> Levels / maps / shops / enemies / items: what must exist and how much variety. Include any procedural or randomized rule and its quality bar (for example "no clipping, no empty space").

### 1.5 Interface
{{Tone and constraints only (simple, goofy, unintrusive). Not layouts.}}

### 1.6 Fun and clarity (hard requirement)
{{The game must be simple to understand, fun, fast and engaging. No design decision may hurt play, hurt engagement, or add confusion. Add the 30-second and 60-second tests (§2.8).}}

---

## PART 2: HOW TO BUILD IT

### 2.1 Engine and language
{{Engine + version + language, one line each. Say it was chosen with the user. If a choice such as Blueprint vs C++ is open, tag it [ASK].}}

### 2.2 Vision and style
> The visual style the user confirmed, the single rule "no model, shader or visual deviation is accepted", and the lineup gate: every new asset is placed beside existing ones under the shared shader and palette and rejected if it does not fit. If the style is still open, tag [ASK] with a recommendation.

### 2.3 Assets
{{Sourcing order (engine primitives, then free CC0 packs, then Blender MCP, generative AI last), a CREDITS.md license ledger, glTF/FBX export rules in one line.}}

### 2.4 Tools and research
{{Research once at the start, verify the tool references in Part 4 are current, pin the result in `_project/TOOLCHAIN.md`. List any tools the user named and what to do with each (use, mine for ideas, skip).}}

### 2.5 Multiplayer and budget
{{Players per room, rooms model (host plus room code), host-authoritative. The budget is $0: no paid services or APIs. Name every requirement that is risky at $0 (voice, NAT traversal, matchmaking) with its free approach and its fallback.}}

### 2.6 Architecture (enforced)
> The user's folder rules, in the engine's vocabulary (paste the architecture example from the engine profile). Must include: folder by category, each folder self-contained; one compact script per trackable category; abstraction only at three seams (networking, game state, events); repetitive logic stays repeated with a sibling comment; `ARCHITECTURE.md` with a one-line-per-folder list and a "where do I find X" table. State that a human new to the engine will review it.

### 2.7 Code style
> The user's simplicity rule: fewest instructions that do the most work, like a careful beginner who writes bug-free code; engine built-ins first, then proven vetted libraries, then custom code; one consistent scripting structure; about 20 lines per function and 300 per file; header comment on every script.

### 2.8 Execution rules
**Phases.** Work in phases, each ending with something demoable and a short report (done, deferred, open questions):
1 Intake (read this, resolve [ASK] items), 2 Toolchain (§2.4), 3 Style (style bible, shared palette and shader, lineup scene), 4 Skeleton (menu, room, empty level, two instances connected if multiplayer),
5 Vertical slice (one level, full loop, fully playable), 6 Content (one category at a time), 7 Hardening (edge cases, performance), 8 Handover (README, `ARCHITECTURE.md`, recipes).
**Gates** (a phase is done only when they pass; a parse check is not a run):
G1 the project boots with zero script errors; G2 the game is launched and the key screen is seen (screenshot saved); G3 rules with numbers or state have tests;
G4 (multiplayer) two real instances connect and finish a round, including full room, late join, host leaving and duplicate names; G5 the edge-case list below is ticked or logged.
**Edge cases.** For every mechanic write what a clumsy, hostile or unlucky player could do (twice at once, worst moment, too fast or never, thing is gone, second playthrough) and handle it.
{{Add the 5-10 game-specific edge cases the discussion surfaced.}}
**Decisions.** Ask only about [ASK] items and choices that are expensive to reverse; decide cheap ones and log them in `DECISIONS.md` (id, decision, reason, reversible?).
**Companion skill.** If the `game-builder` skill is available, use it for the workflow, scaffold and gate scripts. This document stays authoritative.

### 2.9 Definition of done
{{Complete and fully playable from a fresh launch; all gates pass; `CREDITS.md` covers every external asset; a friend who never saw the game can play a full round without help.}}

---

## PART 3: DECISIONS AND ASSUMPTIONS

### 3.1 [ASK] before building
> Numbered list: each an expensive-to-reverse choice with 2-3 options and a recommendation (players per room, camera, platform, voice approach, Blueprint vs C++...).

### 3.2 [DEFAULT] proposed values
> Bullets: each cheap choice with its proposed value (match length, tie-break, bracket count...). Mark each [DEFAULT].

### 3.3 Decided by the builder (not specified here)
{{Gameplay tuning numbers, exact UI layout and art direction details within the style, AI/NPC behavior details, camera feel, sound selection, file-level code structure inside the rules of §2.6, test design. Decide, keep it simple, log it.}}

---

## PART 4: TOOL REFERENCES ({{ENGINE}})
> Paste the engine's Tool References block from `engine-profiles.md`, then the cross-engine block. Adjust only for the user's decisions in the discussion (for example voice not required: delete the voice lines).
````

## 2. Section-by-section guidance

- **1.2 and 1.3** are the heart. Preserve the user's wording and every number they gave (for example "slippery for 30 seconds", "knocked for 3 seconds", "immune for 15 seconds"). Reformat, do not reinterpret.
- **1.4** must carry the user's quality bars as hard requirements ("flawless", "unacceptable"). Convert vague quality words into checkable statements when you can ("validated by loading every combination").
- **2.5** is where infeasible-at-$0 requirements are named, with the free approach and a fallback. Never silently drop a requirement the user wrote; flag it and propose.
- **2.6** must use the engine's vocabulary. A Godot prompt must not say prefab, `.cs` or MonoBehaviour; a Unity prompt must not say `.tscn` or autoload.
- **2.8** is fixed text plus the game-specific edge cases. Keep the gate definitions: they are what stops "done" being claimed after a parse check.
- **3.3** is the user's instruction that "the rest is decided by the agent that makes the game". Always include it.
- **Part 4** is pasted, not paraphrased, so install commands stay exact. Keep *verify* markers.

## 3. Tag convention
Exactly two tags: **[ASK]** and **[DEFAULT]**. Every item in §3.1 is [ASK]; every item in §3.2 is [DEFAULT]. Inline use in other sections is allowed (for example "[ASK] Blueprint or C++?").
Do not invent other tags. The checker warns on unknown bracket tags.

## 4. What to keep verbatim from the user
Their feature list, numbers, quality bars, the architecture rules, the $0 rule, the "simple and fun" requirement, the human-reviewer requirement, and tool links they named.
When cleaning contradictions, keep both intentions and resolve with a rule (for example "folders separate everything, abstraction only at three seams").
Say what you changed in the reply that delivers the prompt, not inside the prompt.

## 5. Length and tone
Typical size is 150-350 lines. Under 60 lines is missing content; over 600 is over-specified (the builder gets to decide the rest). Imperative, plain, no marketing words, no emoji.
