# The pipeline, stage by stage

`SK` is the skill folder and `JOB` the job folder (see SKILL.md, Setup). Every command runs from `SK` (`cd "$SK" && ...`) with `python -I`. `G` below means `"$JOB/gx"`, the galaxy folder, and file paths such as `galaxy/nodes.json` are relative to it. The helpers are in `scripts/gxhelp.py`:

| Helper | Use |
|---|---|
| `python -I scripts/gxhelp.py show G L1 5 12` | print units 5 to 12 of L1 exactly as extracted (one number = one unit, none = all) |
| `python -I scripts/gxhelp.py find G "phrase" [--sid L1]` | where a phrase occurs, with the quote-matching rules: use it to check a quote before you write it |
| `python -I scripts/gxhelp.py nodes "$JOB"` | merge `JOB/notes/nodes/*.json` into `galaxy/nodes.json` |
| `python -I scripts/gxhelp.py coverage "$JOB"` | write `ledger/coverage.json` from `JOB/notes/inventory/` and the node refs, and list gaps |
| `python -I scripts/gxhelp.py order G --sources L1,T1,L2 [--closure a,b]` | main-pathway order (prerequisites first), deviations; `--closure` = ids plus all their prerequisites |
| `python -I scripts/gxhelp.py bar G <nodeId>` | what that node's full lesson must contain, with its key facts and quotes |

Keep `JOB/notes/state.md` current. A good state file is short:
```
galaxyId gx_nosql_s7 | name nosql-s7 | language en | sources in teaching order: L1 T1 L2 T2 L3 L4 L5
exam: final, written, lesson-only (user-stated); duration unknown
focus: exam (scope L1-L5, cram), level L3
done: stages 0-8; lessons 1-6 of 17 (exam pathway order)
next: lessons for shard-key-selection, hash-mod-n-key-routing, ...
```

---

## Stage 0. Intake

Ask once, in one message, with numbered questions. Accept short answers, and use the defaults for anything left unanswered.

1. **Subject**: name, semester or year, and the language the galaxy should be written in (default: the language of the files).
2. **Files**: which files are lectures, TPs/labs/TDs, past papers or other documents, and the order they were taught in. Default: lectures by their number, each TP right after the lecture it practises.
3. **Exam**: the questions in `references/exam.md` (type, format, duration, what is in scope, what the professor said). Default: everything unknown (`null`).
4. **Focus**: which pathways get full lessons:
   - the natural pathway (everything, in teaching order; many turns for a big course);
   - an exam pathway (only what the exam covers, from question 3);
   - a topic ("replication and consistency");
   - a time budget ("I have 6 hours").
   Default: an exam pathway when the exam scope is known. Otherwise a `starter` pathway: the core nodes of the first main stage plus their prerequisites, at most 8 nodes.
5. **Level**: L2 (full lessons) or L3 (full lessons plus a self-audit; slower). Default: L3.

If the user says "just do it", state the defaults you are using in one line and start. Record the answers in `state.md`.

## Stage 1. Set up

```bash
mkdir -p "$JOB"/{inbox,gx/galaxy,notes/inventory,notes/nodes,out}
cp /mnt/user-data/uploads/* "$JOB/inbox/"          # claude.ai; elsewhere copy the files the user named
date -u +%Y-%m-%dT%H:%M:%SZ                         # for createdAt
```

Write `galaxy/meta.json` (that is, `JOB/gx/galaxy/meta.json`):
```json
{ "galaxyId": "gx_nosql_s7", "profile": "galaxy", "title": "NoSQL", "subject": "NoSQL", "semester": "S7",
  "language": "en", "revision": 1, "createdAt": "2026-10-17T17:40:00Z",
  "generator": { "name": "galacticus-maker", "version": "1", "model": "<your model id>" },
  "description": "One paragraph: what the course covers and what this galaxy contains.",
  "examFacts": ["Only what the user said about the exam, in their words"] }
```
`galaxyId` = `gx_` + the subject slug with `_` + the semester, lowercase (`^gx_[a-z0-9_-]{3,80}$`). It never changes afterwards. Omit `examFacts` when the user said nothing about the exam. Choose `<name>` too, the file name of the deliveries (`nosql-s7`), and write both in `state.md`.

## Stage 2. Extract

Give each file a source id in teaching order: lectures `L1, L2, ...`, TPs/labs/TDs `T1, T2, ...`, past papers `P1, ...`, other documents `D1, ...`. Use the course's own numbering when it has one (Lecture 3 = `L3`). Then extract each file:

```bash
cd "$SK" && python -I scripts/extract_units.py "$JOB/inbox/<file>" L1 --role lecture --title "NoSQL Lecture 1" --out "$JOB/gx"
```

- Roles: `lecture | tp | td | project | report | past-paper | other`. One unit per slide (pptx, in the presentation's own slide order, with speaker notes and tables), per page (pdf), or per heading section (docx, md, txt).
- The output line reports image-only and empty units. For each image-only unit, if you can see what it teaches (the slide rendered as an image, the page of a PDF attached to the conversation), transcribe it into that unit's `text` and set `"textState": "transcribed"`. If you cannot read it, leave it; it becomes `no-content` with the reason "image-only, not readable" in stage 3.
- **Exit code 3** (no PDF text extractor): transcribe the pages yourself. Write `sources/units/<sid>.json` as `{"id": "L2", "units": [{"n": 1, "title": "", "text": "<the page's text, word for word>", "notes": "", "tables": [], "textState": "transcribed"}, ...]}` with one unit per page and no gaps. Then add `{"id": "L2", "title": ..., "role": ..., "kind": "pdf", "unitKind": "page", "file": "<file name>", "unitCount": <pages>, "imageOnly": []}` to `sources/index.json`.
- Old formats (`.ppt`, `.doc`): convert them with `soffice --headless --convert-to pptx <file>` (or `docx`) when LibreOffice exists; otherwise ask the user for pptx, docx or pdf.
- Never edit extracted text, and never shorten it. Transcriptions are the only text you write into units.

## Stage 3. Inventory

For each source, in order, read every unit (`gxhelp show G L1 1 10`, then `11 20`, and so on) and write `notes/inventory/<sid>.json`:

```json
{ "id": "L4", "units": [
  { "n": 1, "status": "no-content", "reason": "title slide (course, instructor, year)" },
  { "n": 41, "status": "covered", "items": [
    { "id": "L4-41-1", "what": "hash function: any-size input -> fixed-size output", "niche": false },
    { "id": "L4-41-2", "what": "SHA-1 output = 40 hex digits = 160 bits", "niche": true },
    { "id": "L4-41-3", "what": "'Hello world' vs 'Hello World': completely different SHA-1", "niche": true } ] } ] }
```

- `status`: `covered` (it teaches something) or `no-content`. No-content units are title slides, agendas, section dividers, "Questions?", "Thank you", bibliography pages and unreadable images. Every no-content unit needs a `reason`.
- An **item** is one thing a learner could be asked: a definition, a property, a list or enumeration (the whole list is one item, and so is each surprising member), a number, a name, a date, a default, a command or its syntax, a procedure, an example or case, a comparison, a warning.
- `niche: true` = a small precise detail a professor can ask word for word: numbers, years, names, defaults, thresholds, flags, command names, exact list members. Be generous: niche items are what learners lose marks on.
- Item ids are `<sid>-<n>-<k>`. Nodes list them in `covers`.

## Stage 4. Nodes

Group the items into nodes. Write one file per source, `notes/nodes/<NN>-<sid>.json` = `{"nodes": [...]}` (`01-L1.json`, `02-T1.json`, ... in teaching order), then merge them with `gxhelp nodes "$JOB"`. See `assets/examples/nodes.example.json` for one real node of each kind.

- **One node = one teachable topic** of about 3–15 minutes, usually 1–4 consecutive units. Expect about one node per 2–3 covered units (a 40-slide lecture gives 12–20 nodes). Do not make a node per slide, and do not make one node per lecture.
- A TP that practises a lecture topic goes into the lecture's node (its refs then mix `L` and `T`, and `origin` becomes hybrid). A TP that teaches its own procedure (a command set, a design method) is its own `skill` node.
- `kind`: `concept` (what something is or how it works), `skill` (a procedure the learner performs: commands, design steps, calculations), `event` (a dated origin, person or milestone), `scenario` (a case or situation to analyse). `category`: `technical` for concepts and skills, `historical` for events, `situational` for scenarios.
- `priority`: `core` (central, prerequisite for much else, sure to be examined; about 25–35% of nodes), `standard`, `detail` (side facts).
- `id`: a slug of the label (`hash-function-and-collisions`). `label`: a short noun phrase, at most about 60 characters. `estMin`: 3–15 typically (integer 1–90).
- `card.definition`: 1–3 plain sentences that are true to the course (10–1,200 characters; no quote needed).
- `card.keyFacts`: one Fact per item of the node, and **every niche item must be a key fact**. `text` restates it in a full sentence (4–300 characters); `quote` is the verbatim fragment that proves it; `ref` is its unit. Check doubtful quotes with `gxhelp find`.
- `refs`: every unit the node's items come from. `anchors`: 1–3 `{ref, quote}` headline fragments (a slide title or key sentence). `covers`: the item ids.
- Never write the subject node or the category hubs. They are implicit.

## Stage 5. Coverage ledger

```bash
cd "$SK" && python -I scripts/gxhelp.py coverage "$JOB"
```
It writes `ledger/coverage.json` (`items` and `niche` counts per source, one entry per unit) and lists every covered unit that no node cites, every unit missing from the inventory, and every no-content unit that a node cites. Fix them all (add refs, add a node, or correct a status), then run it again until it reports 0 problems.

## Stage 6. Edges and bubbles

Write `galaxy/edges.json` = `{"edges": [...], "bubbles": [...]}`:

- `requires` (source → target: the target cannot be understood without the source). Use it only for real prerequisites, and keep it sparse: 1–3 per node, never to "everything earlier". It must be acyclic.
- `follows` (consecutive teaching inside one lecture, when there is no stronger link).
- `relates` (a cross-topic link: the same idea in two places, a contrast, a TP practising a concept).
- Every edge has a `why` (one short sentence). Both ends must be existing node ids. No self-loops, and no duplicate pairs.
- `bubbles`: one per `skill` node that practises several concepts: `{"id": "bubble-<skillId>", "skillId": "<skill node>", "memberIds": [the concepts it practises], "tethers": [related scenarios or events]}`. A bubble is optional when a skill practises one concept only.

## Stage 7. Main pathway

```bash
cd "$SK" && python -I scripts/gxhelp.py order "$JOB/gx" --sources L1,T1,L2,T2,L3
```
`--sources` is the teaching order from stage 0. The helper orders the nodes by their first ref in teaching order, and pulls each `requires` prerequisite in just before the first node that needs it. Its `ORDER` line is the node order, and its `DEVIATIONS` line is the `deviations` array: each node that was pulled earlier than its teaching position. Rewrite each `why` in plain words ("Quorums require hashing, which Lecture 4 teaches after them"). If it reports a cycle, turn the weakest `requires` of the cycle into `relates` and run it again.

Then cut the order into stages without changing the order: **6–10 stages** for a module (at most 40); a course of one or two lectures gets 2–5 stages, and the validator's `W-PATHWAY` warning about it is fine.
- Cut at lecture boundaries and at the course's own section dividers (the no-content divider units in the inventory). Put TP nodes in the stage of the lecture they practise.
- A stage has about 5–20 nodes in a module. Merge tiny stages and split huge ones at a divider.
- `title`: the course's own name for that part. `why`: one sentence on what this stage does in the course.

Write `galaxy/pathways.json`:
```json
{ "pathways": [ { "id": "main", "name": "Natural pathway", "kind": "main", "why": "The professor's own teaching order.",
                  "stages": [ { "title": "...", "why": "...", "nodeIds": ["...", "..."] } ] } ],
  "deviations": [ { "nodeId": "kv-get-set-delete", "movedBefore": "meaningful-keys-and-forms", "why": "..." } ] }
```
The main pathway lists **every node exactly once**; when nothing was pulled forward, `deviations` is `[]`. Optional branch pathways (`kind: "branch"`, such as a lab track) list a subset, each node at most once.

## Stage 8. Focus pathways

Add one pathway per focus request to `galaxy/pathways.json`, with `"focus": true`. Its stages reuse the main stages (same titles and order), keeping only the selected nodes, and it drops empty stages.

| Request | Nodes, always in main-pathway order |
|---|---|
| **natural** | the main pathway itself: set `"focus": true` on `main`, and add no new pathway |
| **exam** (`kind: "exam"`, with `scope`) | keep a node if any of its refs is in an in-scope source; drop TP-only nodes (`origin` tp) when no TP is in scope (hybrid nodes stay); keep `historical` nodes only if history questions are expected, else list them in `optional`; keep `detail` nodes only if niche facts are expected or the mode is `mastery`; then add every prerequisite (`gxhelp order ... --closure <ids>`). If `hours` is set and the total `estMin` exceeds it, keep the order and move the lowest-priority remainder to a last stage titled "If time allows" |
| **topic** (`kind: "topic"`) | the nodes whose label, definition or key facts are about the topic, plus their prerequisites (`--closure`). Name it `Topic: <topic>` and give it a slug id |
| **hours** (`kind: "custom"`) | core nodes first, in teaching order, until the minutes are spent, plus their prerequisites |
| **starter** (the default) | the core nodes of the first main stage plus their prerequisites, at most 8 |

```json
{ "id": "exam", "name": "Exam pathway", "kind": "exam", "focus": true,
  "why": "Everything the final covers (L1-L5, no TP), prerequisites first.",
  "scope": { "sources": ["L1", "L2", "L3", "L4", "L5"], "forms": ["niche-fact", "scenario"], "mode": "cram", "hours": null, "notes": "lesson-only" },
  "stages": [ { "title": "...", "why": "...", "nodeIds": ["..."] } ], "optional": ["codd-relational-model-1970"] }
```
A focus pathway is complete when every node in it, its `optional` nodes included, has a lesson at L2 or better (L3 when the level is L3). Count the focus nodes and plan the turns: about 6–8 lessons per turn.

## Stage 9. Lessons

Read `references/lessons.md` before the first lesson. Then, for each focus node in pathway order (so that prerequisites are written first):

1. `gxhelp bar G <nodeId>`: the bar to meet, the `needs` and `related` candidates, and the key facts with their quotes.
2. `gxhelp show G <sid> <n>` for each unit in the node's refs. Write from the units, not from memory.
3. Write `lessons/<nodeId>.json` in one file write.
4. For L3, do the audit loop (lessons.md), fix the lesson, and record `audit`.
5. Every 2–3 lessons, run `validate` and fix `E-QUOTE`, `E-PRIM`, `E-QUESTION` and `W-FILL` for those files before you go on.

## Stage 10. Main guide

Write `guide/main.json` with the seven sections in this order (model: `assets/examples/main-guide.example.json`). Every item with a `ref` carries a verbatim `quote`. Items without a ref are study guidance and never course claims.

| `kind` | Items |
|---|---|
| `howto` | 3–5 items on how to use the guide, the map and the pathways (no refs) |
| `map` | one item per main stage: "Stage 2, <title> - 14 nodes, 5 core, about 80 min. <why>" (no refs) |
| `reference` | the must-know definitions and rules: about one per core node, `ref` + `quote` |
| `niche` | **every** niche key fact of the galaxy, in teaching order, `ref` + `quote` (it is long, and that is the point) |
| `traps` | where marks are lost: "Trap: ..." items from the lessons' trap sections and the classic confusions, with `ref` + `quote` when the course states it |
| `checklist` | 6–10 night-before actions (no refs) |
| `route` | the core nodes in main-pathway order, one item each, "<label> - <why it matters> (about N min)" (no refs) |

Each section has `id` (its kind), `kind`, `title` and a one-sentence `intro`.

## Stage 11. Exam

Follow `references/exam.md`: write `exam/profiles.json` (always, unknowns as `null`) and `exam/mock.json` (when the user wants a practice paper, or by default for a galaxy; at least one question per form of the profile).

## Stage 12. Report and README

Run `validate` and then `stats "$JOB/gx"` first: copy the fill counts and the focus numbers from `stats` into the report. Write `work/report.json`:
```json
{ "workOrderId": null, "generator": { "name": "galacticus-maker", "version": "1", "model": "<model>" },
  "done": ["122 nodes from 9 sources (279 units)", "exam pathway: 17 nodes at L3", "main guide", "practice paper, 18 questions"],
  "notDone": ["L5 slides 12-14 are image-only and could not be read", "the natural pathway is at L1 outside the exam pathway"],
  "fill": { "L1": 105, "L2": 0, "L3": 17 }, "focus": { "exam": { "nodes": 17, "full": 17 } },
  "questions": ["Is Lecture 5 in the exam?"], "notes": "Anything the learner should know." }
```
`workOrderId` is the work order's id for a handoff, otherwise `null` or omitted. `README.txt` (at the root of the galaxy folder) is plain text: title, what is inside, how to open it ("open <name>.html in a browser, or import <name>.galaxy into Galacticus"), the generator and date, "The practice paper is not the professor's exam", and "Course content belongs to its authors: share only with people who have access to the course".

## Stage 13. Validate, pack, stamp, deliver

```bash
cd "$SK" && python -I scripts/gxformat.py validate "$JOB/gx"          # until RESULT: OK, 0 errors
cd "$SK" && python -I scripts/gxformat.py stats "$JOB/gx"             # fill and focus at a glance
cd "$SK" && python -I scripts/gxformat.py pack "$JOB/gx" "$JOB/out/<name>.galaxy"
cd "$SK" && python -I scripts/gxformat.py html "$JOB/out/<name>.galaxy" "$SK/assets/galacticus-reader.html" "$JOB/out/<name>.html"
```
`pack` writes `manifest.json` into the folder and the zip (`Verified` in the reader). `notes/`, `inbox/` and `out/` are outside the galaxy folder, so they are never packed. On claude.ai, copy the two files from `out/` to `/mnt/user-data/outputs/`.

**Later turns** ("continue"): read `state.md`, write the next lessons, bump `revision` in `galaxy/meta.json`, and update `work/report.json`. Since `pack` left a `manifest.json` in the folder, `validate` now reports `E-HASH` for every changed file: run `manifest "$JOB/gx"` first, then validate, pack and stamp again. Each delivery is a complete, valid galaxy.

## Sizes that work

| Course | Units | Nodes | Turns (L1 skeleton) | Full lessons per turn |
|---|---|---|---|---|
| one lecture | 20–50 | 8–20 | 1 | 6–8 |
| a module (4–6 lectures + TPs) | 150–300 | 60–130 | 3–5 (inventory one or two sources per turn) | 6–8 |

If the context gets long, finish the current file, validate, write `state.md`, deliver what exists, and stop with: "N of M focus lessons done. Say continue for the next batch."
