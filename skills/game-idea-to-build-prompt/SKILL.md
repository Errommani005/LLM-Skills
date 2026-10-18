---
name: game-idea-to-build-prompt
description: Guides the full workflow for turning a game idea into a complete build prompt for a coding agent (Claude Code or similar), through discussion first. Trigger whenever the user pitches or describes a game idea and wants help developing it, especially requests for a "build prompt", "coding prompt" or "brief" for a game, help thinking through mechanics, game vision, style, engine choice (Godot, Unity, Unreal Engine 5) or toolchain (MCP servers, skills, agents, voice chat, multiplayer) before development starts, or cleaning up an existing game prompt. Also trigger on follow-ups like "add this mechanic to the prompt", "update the prompt", "switch the engine", or "what tools should the agent use". Covers capturing the idea, mechanics and $0 feasibility, style and engine recommendation, a toolchain round, writing the structured prompt (vision, mechanics, architecture and execution rules, engine tool references), verifying it, and iterating.
---

# Game Idea to Build Prompt

Turn a game idea into **one deliverable: a build prompt** addressed to the coding agent, after a short discussion that settles the vision, mechanics and toolchain.
The prompt states **what** the game is and **which constraints** the build follows (architecture, execution rules, tool references). The building agent decides the rest and logs it.
No game is built in this skill, and no concept artifact is required: the output is a Markdown prompt (plus a short discussion before it).

Companion: the `game-builder` skill holds the full standard, genre playbook, engine tool lists, agents and scripts. This skill works without it: the prompt it writes is self-contained and
mentions `game-builder` only as optional.

## Workflow at a glance
1. **Capture the idea** (first message: read everything, reflect it back, one discussion round)
2. **Discuss mechanics and feasibility** (suggestions and $0 risks, nothing applied until accepted)
3. **Vision and style** (recommend a style with reasons, get confirmation)
4. **Toolchain round** (engine, editor MCP, skills, assets, networking/voice, tests)
5. **Write the build prompt** (template, engine profile blocks, user's words preserved)
6. **Verify, deliver, iterate** (`scripts/check_prompt.py`, short summary, then keep the prompt in sync)

Do not skip ahead. If the user's first message is already a detailed spec (a long list of mechanics and rules), compress stages 1-3 into one reply: reflect, flag risks, ask the few missing questions,
and move to the toolchain round. If they say "just write it", write it with gaps tagged `[ASK]` or `[DEFAULT]`.

## Stage 1: Capture the idea
Read the whole message, including lists, links, and any "etc." Then reply with:
1. **One line** proving you understood the pitch, in their words.
2. **A discussion round** (`references/discussion-guide.md` section 1): at most 5 questions (only what is missing and changes the game) and at most 6 tagged suggestions.
3. What happens next, in one sentence.
If the idea is vague ("a fun party game"), ask for the core loop first: what the player does every ten seconds and what makes it fun. Offer 2-3 concrete options.
If the user pasted an existing prompt, treat it as the spec: preserve every instruction, number and architecture rule, and list contradictions you found (for example "separate everything into folders" versus "do not over-modularize") with a resolution rule for each.

## Stage 2: Discuss mechanics and feasibility
- Reflect their mechanics back with their numbers. Suggest by **category** (feel, clarity, fairness, variety, scope, risk, social) using their own mechanics as raw material.
- Raise every **$0 risk** the spec implies (`discussion-guide.md` section 5: voice chat, internet rooms, matchmaking, random content without clipping...) with a free route and a fallback. Never drop a requirement silently.
- Keep a running list of decisions: **[ASK]** (expensive to reverse: core loop, players, camera, platform, style, engine) and **[DEFAULT]** (cheap: timers, tie-breaks, tiers).
- Apply nothing the user did not accept. If a suggestion conflicts with their spec, say so and let them choose.
- Stay game-first: no engine talk until the game is clear unless the user raises it.

## Stage 3: Vision and style
Recommend a visual style with reasons tied to this game and to ease of agent implementation (`discussion-guide.md` section 7). Offer the options, recommend one, ask for confirmation. Agree with the user's lean when it fits and say honestly when another fits better.
Whatever is confirmed becomes the "no deviation" rule and the lineup gate in the prompt. If the user cannot decide, tag it `[ASK]` with your recommendation so the builder confirms before producing assets.

## Stage 4: Toolchain round
Present, concisely, using `references/engine-profiles.md`:
1. **Engine** table with a recommendation (default Godot for simple/goofy/low-poly/friends/$0). This is the one fork to confirm. Unity and Unreal are fully supported; Unreal also needs a Blueprint-vs-C++ answer.
2. **Editor-control MCP** (one per engine), **skill bundle** and the two or three cross-engine skills that match the game, **assets** (Blender MCP, CC0 sources), **networking and voice** default with free route and fallback, **tests and release**.
3. **Every tool or link the user named**: say use / mine for ideas / skip, with one honest reason.
Mark anything unconfirmed as *verify* and say why. Ask "anything to change?" once. Record the result; it becomes Part 4.
Do not re-research each time: the profiles are verified as of October 2026. If the conversation is much later, or the user asks for "latest", run a quick check of the main tools before pasting (versions, licenses, free tiers).

## Stage 5: Write the build prompt
Use `references/prompt-template.md` (skeleton plus guidance) and the matching block from `references/engine-profiles.md`. See `references/worked-example-mall-stormers.md` for a finished example.
Rules:
- **Preserve the user's words, numbers and quality bars.** Reformat and group; do not reinterpret or soften ("unacceptable" stays a hard requirement).
- **State what and which constraints, never how**, unless the user specified how. Part 3.3 ("decided by the builder") explicitly hands the rest to the building agent.
- **Part 2.6 uses the engine's vocabulary** (Godot: `.gd`, scenes, autoloads; Unity: `.cs`, prefabs; Unreal: C++ classes, Blueprint subclasses). Never mix.
- **Tag only with `[ASK]` and `[DEFAULT]`**; number every section; reference sections as `§N.N`.
- **Part 4 is pasted verbatim** from the engine profile (install commands stay exact), adjusted only for the user's decisions (for example delete voice lines if voice is not wanted).
- Include the fixed execution rules (phases, gates G1-G5, edge-case instruction, decision rule), the $0 budget, the human-reviewer requirement and the 30/60-second tests.
- Add the 5-10 game-specific edge cases the discussion surfaced to §2.8.
- Deliver the prompt in **one code block** (so it can be copied whole) after a two-to-four line summary of what it contains.

## Stage 6: Verify, deliver, iterate
1. Save the prompt to a file and run `python scripts/check_prompt.py <file>`. Fix every ERROR and read every WARN. Do not show the prompt until it is clean or the warnings are consciously accepted.
2. Reply with: the prompt (one code block), then **what you changed from the user's input** (contradictions resolved, Unity-style words converted, anything you flagged or added), then the **items needing their answer** (`[ASK]` list). Keep it short.
3. **Iterate:** on follow-ups ("add a banana-peel item", "make it Unity", "drop voice chat"), update only the affected sections, re-run the checker, and say what changed. An engine change swaps §2.1, the §2.6 vocabulary and Part 4 together.
   Own mistakes plainly. Keep the prompt and the conversation consistent: if a decision changes, check every section that mentions it.

## Principles
- **Fidelity first:** the user's vision, mechanics and rules are intact in the output.
- **Honesty about cost:** a requirement that cannot be done at $0 is flagged with a free route and a fallback, never hidden or silently weakened.
- **Builder autonomy:** the prompt constrains and verifies; it does not micro-manage. Fewer, firmer rules beat many soft ones (heavy process measurably hurts).
- **Evidence over claims:** the prompt requires gates that run and see the game, because a parse check is not a run.
- **Right amount:** discussion rounds are short; one more round beats a vague prompt, but never block on questions the user does not want to answer.

## Failure modes to avoid
- Over-specifying implementation, algorithms or UI layouts the user never decided.
- Asking expensive questions twice, or asking cheap ones at all.
- Writing "bug-free" without gates, or "free" without checking the terms.
- Letting Unity or Unreal words leak into a Godot prompt (and the reverse).
- Pasting a stale tool list without *verify* markers or without telling the builder to pin versions once.
- Dropping a hard requirement (voice, flawless randomization) because it is hard.
- Adding features the user did not ask for and presenting them as part of the spec.

## Reference index
| File | Read when |
|---|---|
| `references/discussion-guide.md` | Stages 1-4: question bank, suggestion categories, per-genre questions, $0 feasibility table, toolchain round, style framework, readiness check |
| `references/prompt-template.md` | Stage 5: the skeleton and guidance for each section |
| `references/engine-profiles.md` | Stage 4-5: engine table, vocabulary, architecture examples, paste-ready Tool References blocks for Godot, Unity, Unreal |
| `references/worked-example-mall-stormers.md` | Stage 5: a complete finished prompt to match in format |
| `scripts/check_prompt.py` | Stage 6: validates sections, placeholders, tags, `§` references, engine vocabulary, budget, gates, tool references |
