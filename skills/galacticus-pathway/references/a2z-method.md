# The A-to-Z method

How to turn one lesson, chapter or topic into an ordered course that a beginner can follow from the first word to exam-level mastery. The format rules are in `FORMAT.md` (§9.2 bar, §13 pathway profile); this file is about the teaching decisions.

## 1. Scope: find everything that teaches the topic

A topic is rarely on consecutive slides only. Before planning, collect every unit that teaches it:

- **Search the terms** and their synonyms with `a2z.py find` (for replication: "replica", "quorum", "consisten", "master", "two-phase", "CAP"). Use stems: the matcher is a plain substring search after normalization.
- **Follow repeats.** Courses often repeat a block of slides in the next lecture (in the dogfood course L2#28–31 are word for word L3#3–6). Cite one copy in the lessons and list both in the node's `refs`; say so in the report.
- **Pull in practice.** Labs and TPs that apply the idea (commands, set-ups, measurements), exercises, and review or answer slides (they often state the cleanest definitions).
- **Read the neighbours.** `a2z.py show <sid> <n-2> <n+2>` around each hit: the slide before often introduces the vocabulary, the slide after has the example.
- **Stop at the topic's edge.** Units that only mention the topic in passing belong to another course; if a prerequisite is taught elsewhere in the sources, cite it in a `prereq` section instead of re-teaching it.

Write the inventory (`JOB/notes/inventory.md`): per unit, every fact, number, name, command, example and exercise, and whether the exercise has an answer in the sources.

## 2. Order from zero: four layers

Every step may only use words and ideas that earlier steps taught. Build the order in four layers, in this sequence:

| Layer | What goes there | Typical primitives |
|---|---|---|
| **1. Vocabulary and prerequisites** | the words the lesson assumes (cluster, replica, transaction...), why the topic exists, the problem it solves | `text`, `flow` (the problem), `compare` (before/after), `chooser` (recognise the term) |
| **2. Mechanisms** | how each thing works, one mechanism per step, the simplest model first and its alternative next (one writer, then many writers) | `flow`, `stepper`, `quorum`, `kvrepl`, `timeline` |
| **3. Practice** | the lab: commands, set-ups, calculations, measurements, failure drills | `kvrepl`, `stepper`, worked `text` |
| **4. Synthesis** | scenarios that need several steps at once, comparisons across the whole topic, the cumulative traps | `chooser`, `compare`, `stepper` |

Rules of thumb:
- **Course order versus learning order.** Keep the course's order when it already builds up. Deviate when a later slide holds the vocabulary that an earlier slide assumes, and record each move in `pathways.json` `deviations` with the reason (the dogfood course teaches the replication models before CAP, the reverse of the lectures, because CAP is about replicas).
- **Contrast pairs** (ACID/BASE, master-slave/masterless, range/hash) are either one step with a `compare` slide, or two consecutive steps where the second opens by contrasting with the first. Never separate them by unrelated steps.
- **Practice can live inside a mechanism step** when the lab is small (the dogfood's Redis lab is inside the master-slave step). Give it its own step when it has several tasks or needs its own checkpoint.
- **The last stage is synthesis**, even for a narrow topic. It teaches nothing new: it makes the learner choose.

## 3. How many steps and stages

| Input | Steps | Stages |
|---|---|---|
| A narrow topic (a few slides, one section) | 4–8 | 3–4 |
| One lecture | 8–20 | 4–7 |
| A long lecture or a chapter | 15–40 | 6–10 |

Size each step by its facts and minutes: about **5–13 key facts** and **8–15 minutes** (`estMin`). Merge a step with fewer than 4 facts into its neighbour; split a step above about 13 facts, or one that holds two independent mechanisms. A time budget from the user caps the total of `estMin`: drop detail steps first, never the synthesis step.

Stages (3–10, FORMAT.md §13) group steps of the same layer. A stage `title` says what the learner gains ("Two ways to organise the copies"), its `why` says why it comes at this point.

## 4. Priority and kind

- `core`: steps the rest depends on, and the synthesis step. The bar: 5–9 sections, 6–9 slides (2+ interactive), 4–5 questions (1+ not mcq).
- `standard`: a mechanism or lab that nothing later depends on. 4–9 sections, 4–9 slides (1+ interactive), 3–5 questions.
- `detail`: niche facts only (a list of products, a history of names). 3–7 sections and slides, 2–4 questions.

`kind` is `concept` by default; `skill` for a lab or procedure step, `scenario` for the synthesis step (with `category: situational`). Prefer core when in doubt: an A-to-Z course is short, and every step should be complete.

## 5. Checkpoints that build up

Each step ends with 4–5 questions (core). Make them climb:

1. **Recall** (`mcq`, `fill`): the step's definitions and numbers, with the classic wrong answers as options.
2. **Apply** (`multi`, `short`): a worked example of this step ("which statements about the 3-replica example are true").
3. **Connect** (from the third step on, at least one question): a question that needs an earlier step too (the quorum step asks why the write threshold protects durability, which needs the replica vocabulary of step 1). The question's `ref` and `quote` still come from one unit.
4. The **synthesis step's** checkpoint is all scenarios.

Put the trap of each question in `trap` (the classic mistake), and make every wrong `mcq` option plausible: taken from a neighbouring idea, never absurd.

## 6. The A-to-Z guide (`guide/main.json`)

The whole course on one page, built only from the steps' facts (each item with a `ref` has its verbatim `quote`; items without a ref are study guidance, never course claims). All seven sections, in this order:

| Section | What to put in it |
|---|---|
| `howto` | how to use the course: play the steps in order, answer each checkpoint, what "authored" means here |
| `map` | one item per stage: what it teaches, with the quote that best sums it up |
| `reference` | every must-know definition and rule, one item each, word-for-word quotes |
| `niche` | every small number, name, date, port, command and example value |
| `traps` | one item per classic confusion, cumulative across steps |
| `checklist` | one "I can ..." line per step, without refs |
| `route` | the core-first order. When every step is core, say so: the route is the A-to-Z order itself. Never claim which topics "carry the most marks" unless the user told you |

## 7. The final quiz (`exam/mock.json`)

- 10–30 questions; at least one per step; more on core steps.
- **New** wording and new cases: do not copy checkpoint questions.
- All four types (`mcq`, `multi`, `fill`, `short`); `form` on each question (`recall`, `niche-fact`, `scenario`, `command`, `compare`, `design`), `points` in multiples of 0.5, `nodeIds` = the steps it tests.
- Blueprint: one section per form you used; section `count` and `points` add up to the number of questions and `totalPoints`.
- `profile`: `{subject, confidence: "inferred", notes: "FINAL QUIZ of this course, a practice check, not the professor's exam..."}`. `durationMin` is your suggestion for this quiz (about 1.5 to 2 minutes per point); say in the notes that it is the quiz's own design. Never present it as the real exam's duration or format.

## 8. Worked plan: "Replication, quorums and consistency"

Sources: NoSQL lectures L1–L5 and the Redis lab T3. 7 steps, 5 stages, 87 minutes, all core, all L3.

| # | Stage (layer) | Step | Main units | Interactive slides |
|---|---|---|---|---|
| 1 | Zero: why databases keep copies (vocabulary) | replication-and-replicas | L1#33, L1#36, L4#18, L4#38, L5#16 | flow (idle backup to cluster), stepper (scale up/out), compare (fewer/more replicas), chooser (how many copies) |
| 2 | Two ways to organise the copies (mechanism + practice) | master-slave-replication | L4#9, L4#35, T3#25–29 | flow, kvrepl (the real Redis lab commands), stepper (manual failover), chooser, compare |
| 3 | same | masterless-replication-and-ring | L4#10, L4#35–37, L5#16, T3#30 | compare, flow (8-node ring), stepper (node failure), kvrepl (write conflict), chooser |
| 4 | What consistency costs (mechanism) | cap-theorem-and-two-phase-commit | L3#3–6 (= L2#28–31) | stepper, compare, flow (2PC), kvrepl (commit/rollback), chooser (CA/CP/AP) |
| 5 | same | read-write-quorums | L3#9, L4#39, L4#45 | quorum (5 replicas), flow, kvrepl, compare, chooser |
| 6 | Living with eventual consistency (mechanism) | eventual-consistency-and-base | L3#10–13, L4#39 | compare, timeline, stepper, chooser, kvrepl (order matters) |
| 7 | Synthesis | replication-design-scenarios | L3#7, L3#8, T3#25–30 | chooser, compare, stepper, quorum, flow |

Decisions worth copying:
- Step 1 is pure vocabulary: nothing else could start from zero.
- CAP moved after the replication models (a recorded deviation): the learner meets replicas before the theorem about them.
- The lab's exercises without answer keys (L3#8, T3#30) are answered in sections marked authored, and the report says so.
- The overlap rule `R + W > N` is not in the course: it appears only in authored sections and slides, and a trap reminds the learner not to quote it as the course.
