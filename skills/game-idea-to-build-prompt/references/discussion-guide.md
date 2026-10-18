# Discussion Guide

How to run the conversation before writing the prompt. The goal is a shared, concrete picture of the game and its toolchain, reached in few rounds, never an interrogation.

## Contents
1. Shape of a discussion round
2. Question bank (ask only what is missing)
3. Suggestion categories
4. Per-genre extra questions
5. Feasibility flags at $0
6. The toolchain round
7. Style recommendation framework
8. Readiness check

## 1. Shape of a discussion round
Every round has two parts, kept short:
- **Questions** (at most 5): only what is missing or ambiguous and changes the game. Each question names its options and your recommendation.
- **Suggestions** (at most 6): ideas that improve fun, clarity or feasibility, each tagged with a category (section 3) and a one-line reason. Suggestions are proposals: **apply nothing to the user's spec until they accept**.
Open with one line showing you understood the pitch (their words, not a rewrite). Close by saying what happens next ("answer what you want, ignore the rest; I will default the rest and show you").
Never block on questions: if the user says "you decide", decide and log it. Use the ask-user tool (tappable options) when it is available, otherwise numbered questions.

## 2. Question bank (ask only what is missing)
Expensive to reverse (ask):
- **Core loop:** "What does the player do every 10 seconds, and what makes it fun?"
- **Players and session:** solo, local, or online rooms? How many? How long is one session or round?
- **Camera and controls:** first person, third person, top-down, side-scroll? Keyboard/mouse, controller, touch?
- **Platform:** PC, web, mobile? Target hardware (default: integrated graphics at 60 FPS)?
- **Look:** 2D or 3D, and style (section 7).
- **Engine and tools:** section 6.
- **Voice, matchmaking or other expensive features:** needed, or nice to have? (section 5)
Cheap to reverse (decide and log, mention only if they shape the game): colors, key bindings, timer lengths, tie-breaks, number of tiers, respawn rules, UI placement.
Never ask what the user already answered. Never ask more than five at once.

## 3. Suggestion categories
Tag each suggestion so the user can scan:
- **Feel:** feedback on every action (sound, motion, flash), weight and momentum, camera shake budget.
- **Clarity:** how a new player understands the goal in 30 seconds without text; readable silhouettes and colors.
- **Fairness:** anti-frustration rules (immunity after being knocked down, spawn protection, catch-up for the player behind, no stun-lock).
- **Variety:** content that changes between matches without breaking clarity.
- **Scope:** what to cut or phase to keep the game finishable (the genre scope cap in `game-builder`'s `genres.md`).
- **Risk:** a requirement that is expensive, fragile or impossible at $0, with the free alternative.
- **Social:** moments that make friends laugh (chaos tools, goofy results titles, replay moments).
Good suggestions come from the user's own game: reflect their mechanics back ("you have slippery floors and knockdown, so a banana-peel item would reuse both").

## 4. Per-genre extra questions (pick 2-3 for the game's type)
- **Party / co-op:** What do players do *together* vs *against* each other? What happens when someone disconnects? Can late players join? Is there friendly fire? What makes a round end?
- **Platformer:** Precision or forgiving? Checkpoints or lives? Collectibles that matter? Level length?
- **Shooter:** Aim style (twin-stick, first person)? Weapon count? Enemy telegraphing? Cover or movement-driven?
- **Racing:** Arcade or simulation (recommend arcade)? Items/power-ups? Number of tracks and cars? AI opponents?
- **Puzzle:** Real-time or turn-based? Undo? Handcrafted levels or generated? One-sentence rule?
- **Strategy / tower defense:** Pausable? Number of unit types? Map count? Skirmish vs campaign?
- **Survival / crafting:** One biome first? Save system? Multiplayer world ownership? What is the main threat?
- **Narrative:** Choices that change endings? Length? Save/skip/backlog? Art style?
- **Arcade:** Score rule? Difficulty curve? Instant restart? Daily seed?

## 5. Feasibility flags at $0
Raise these as **Risk** suggestions the moment the user's spec implies them. Never silently drop a requirement; propose the free route and a fallback.

| Requirement | Why risky at $0 | Free route | Fallback |
|---|---|---|---|
| **Proximity voice chat** | No engine ships a free voice stack; paid SDKs are common | Godot: TwoVoip (MIT, Opus). Unity: OpenVoiceSharp with own transport. Unreal: EOS Voice (verify) | Discord + in-game speaking indicator |
| **Online rooms across the internet** | NAT blocks hosting; relays cost money | Host + room code reached over LAN, free VPN overlay, UPnP, or port forward | LAN/VPN play; another friend hosts |
| **Matchmaking with strangers, ranked** | Needs always-on servers | None | Friends-only rooms |
| **Anti-cheat** | Needs servers and expertise | Host validates requests | Accept for friend games |
| **Dedicated servers, large player counts** | Hosting cost | None | Small rooms (2-8) |
| **Realistic physics for many objects** | Frame rate and sync cost | Cap bodies, let them sleep, host simulates | Fewer, chunkier objects |
| **Random content placement with zero defects** | Combinatorial clipping bugs | Size-class slots; every piece built to fit its class; validation script over all combinations | Smaller pool |
| **Generative AI for assets/dialogue at runtime** | Paid APIs, style drift | CC0 packs + Blender MCP | Handmade |
| **Browser play with multiplayer** | No UDP in browsers | WebRTC + free signaling | Desktop builds |
| **Mobile + PC with one build** | Input, performance, store fees | One codebase, Compatibility/URP | Pick one platform first |
| **Voice/text moderation, accounts, cloud saves** | Backend costs | Local saves only | None |

## 6. The toolchain round
After the game is clear and before writing the prompt, run a short toolchain round. Present, do not lecture:
1. **Engine** table (`engine-profiles.md` section 1) with a recommendation and one-line reasons. Get a confirmation: this is the one real fork.
2. **Editor control:** name the MCP server the profile defaults to and why (verified, free, maintained). Mention the one alternative.
3. **Skills:** the engine skill bundle and the two or three cross-engine skills that match the game (for example `game-feel`, `level-design`, the genre skill).
4. **Assets:** Blender MCP plus free CC0 sources; note that generative asset services are off by default.
5. **Networking and voice:** the default for the engine, the free route, the fallback (section 5).
6. **Tests and release:** the engine's test framework and the $0 release path.
7. **Anything the user named** (links they gave): say for each *use / mine for ideas / skip*, with one honest line of reasoning.
Ask: "Anything here you want changed?" Then record the outcome; it becomes Part 4 of the prompt.
Mark unverified items *verify* and say so plainly. Never claim a tool is free without checking its terms: say which ones the builder must verify.

## 7. Style recommendation framework
Offer the three options from the user's perspective, then recommend one with reasons tied to *this game* and to ease of agent implementation:
| Style | Best for | Agent-friendliness |
|---|---|---|
| Low-poly (flat/toon) | Most 3D games; free CC0 packs exist in this style | High |
| Simple-geometry blobs (Fall Guys / Among Us 3D) | Party games with identical bean-like players | High: capsules and spheres, minimal rigging |
| Goofy old-school 3D (Goat Simulator style) | Comedy physics, where jank is the joke | Low: charm depends on janky physics; hard to keep consistent |
| 2D pixel / vector | Platformers, puzzle, narrative | Medium / High |
If the user already leans somewhere, agree if it fits, or say honestly why another fits better. Whatever they pick becomes the "no deviation" rule in §2.2.

## 8. Readiness check (before writing the prompt)
Write the prompt when you can answer yes to all:
- [ ] I can state the pitch, the goal, how it ends, and what makes it fun in my own words, and the user would agree.
- [ ] Every mechanic the user listed is captured with their numbers.
- [ ] Players, camera, platform, style, engine are decided or tagged [ASK].
- [ ] Every $0-risky requirement has a free route and a fallback.
- [ ] I know which choices are [DEFAULT] and which the builder owns.
If not ready, run one more short round rather than writing a vague prompt. If the user says "just write it", write it with the gaps tagged [ASK] or [DEFAULT].
