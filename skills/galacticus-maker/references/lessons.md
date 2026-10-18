# Writing full lessons (L2 and L3)

A lesson is `lessons/<nodeId>.json`: a **guide** to read, a **presentation** of slides (several of them interactive), and a **checkpoint** quiz. The complete real model is `assets/examples/lesson.example.json` (an L3 lesson using all 8 primitives and all 4 question types). Read it once before your first lesson.

```json
{ "nodeId": "quorum-and-replication-factor",
  "guide": { "index": ["You need", "What a quorum is", "...", "Recap"],
             "sections": [ GuideSection, ... ],
             "needs":   [ { "nodeId": "cap-theorem-and-consistency", "why": "Quorums are a dial on the CAP trade-off." } ],
             "related": [ { "nodeId": "master-slave-replication", "why": "Another way to keep replicas." } ] },
  "slides": [ Slide, ... ],
  "checkpoint": [ Question, ... ],
  "audit": { "by": "<model> self-audit", "refuted": 3, "fixed": 3, "at": "2026-10-17T18:00:00Z", "note": "what was wrong and fixed" } }
```
- `guide.index` lists the section titles in order.
- `needs` = the node's `requires` prerequisites (from `gxhelp bar`), each with a `why`. `related` = `relates` neighbours and the nodes this one unlocks. Every `nodeId` must exist.
- Leave out `audit` for L2. Add it only after a real audit pass (L3, below).

## 1. The bar (FORMAT.md §9.2)

Below the minimum, the lesson counts as L1 and a focus pathway fails (`E-FOCUS`). Above the maximum, you get a warning.

| Node priority | Guide sections | Slides | Interactive slides (not `text`) | Checkpoint questions |
|---|---|---|---|---|
| `core` | 5–9; first `prereq` when the node has a prerequisite (an incoming `requires` edge or a `needs` entry); last `recap` | 6–9 | ≥ 2 | 4–5, ≥ 1 that is not `mcq` |
| `standard` | 4–9, last `recap` | 4–9 | ≥ 1 | 3–5 |
| `detail` | 3–7 | 3–7 | ≥ 1 | 2–4 |

Also: every key fact of the node's card should appear in the guide or the slides (`gxhelp bar` lists them). Add a `trap` section when the course has a classic confusion on this node.

A shape that works for a core node: `prereq` → `definition` → 2–4 of `technique | example | summary | formula | command | history | scenario` → `trap` → `recap`, and 7–8 slides: one `compare` or `flow` for the mechanism, one sandbox (`quorum`, `kvrepl`) or a `stepper` to walk through it, one `chooser` to apply it, and a closing `text` recap.

## 2. Guide sections

```json
{ "id": "s-trap", "title": "Traps", "kind": "trap", "body": "markdown-lite", "facts": [Fact], "refs": ["L3#10"], "provenance": "authored" }
```

| `kind` | Write |
|---|---|
| `prereq` | what the learner must already know and why, naming the nodes. It never re-teaches them. It has no facts |
| `definition` | the definition in the course's words, with its facts |
| `summary` | a synthesis of several units, such as a trade-off or the properties side by side |
| `formula` | the formula in backticks, each symbol explained |
| `technique` | a procedure or rule of thumb, step by step |
| `example` | a worked example. Use the course's own example when there is one; an example you invent is `"provenance": "authored"` |
| `trap` | one `- Trap: ...` line per trap |
| `recap` | 3–6 `- ` lines: the facts to remember, and what comes next in the course |
| `history` | dates, people and the order of events |
| `scenario` | a situation from the course and how the concept applies |
| `command` | the command or syntax in backticks, with its options and output |

- `body` is markdown-lite: `**bold**`, `` `code` ``, lines starting with `- `, blank lines between paragraphs, and bare refs such as `L4#41` (they become source chips). No HTML, links, images or `#` headings.
- `facts`: the course claims of this section, each `{text, ref, quote}` with a verbatim quote. Put a node's key facts here (or on slides) so the lesson teaches every one of them.
- `refs`: the units the section draws on.
- `"provenance": "authored"` marks content you wrote that the course does not state: analogies, invented examples, readings between the lines, rules of thumb. Authored content still gets `refs` (the units it extends). It may carry `facts` for the course claims it uses. Never present an authored claim as course content.

Real sections:

#### `prereq` (lesson `shard-key-selection`)
```json
{
 "id": "prereq",
 "kind": "prereq",
 "title": "You need",
 "body": "You need to know how **range-based**, **hashed**, **geographic** and **directory** sharding assign a record to a shard.\nThis lesson does not re-teach them. It asks one question: given a strategy, is the key you picked a good one, and if not, what fixes it?"
}
```

#### `definition` (lesson `codd-relational-model-1970`)
```json
{
 "id": "s3",
 "kind": "definition",
 "title": "Structural independence",
 "refs": ["L1#9"],
 "body": "**Structural independence** is called 'the breakthrough'. The **logical** organization of data (how you think of it and ask for it) is separated from how it is **physically stored**.\n\nConsequence: programs no longer break when storage changes.",
 "facts": [
  {
   "ref": "L1#9",
   "text": "The logical organization of data is separated from how it is physically stored, so programs no longer break when storage changes.",
   "quote": "The logical organization of data is separated from how it is physically stored."
  }
 ]
}
```

#### `trap, authored` (lesson `quorum-and-replication-factor`)
```json
{
 "id": "traps",
 "kind": "trap",
 "title": "Traps",
 "refs": ["L3#9", "L4#38", "L4#39"],
 "provenance": "authored",
 "body": "- Trap: read threshold 1 is fastest but may be stale; read threshold equal to the replica count is consistent but slowest.\n- Trap: write threshold 1 means losing that one server loses the data. The fix is a threshold of at least 2, with more replicas than the threshold.\n- Trap: fewer replicas is a legitimate choice, but only when data is easy to regenerate and reload.\n- Trap: the quorum sandbox shows R + W against N as an overlap rule of thumb. The course slides state the trade-offs, not that formula, so use it as intuition and quote the slide facts in answers."
}
```

#### `example, authored` (lesson `codd-relational-model-1970`)
```json
{
 "id": "s5",
 "kind": "example",
 "title": "Worked example: asking for data",
 "refs": ["L1#14", "L1#9"],
 "provenance": "authored",
 "body": "Take the course's own sample table from the SQL slides: `employees` with `emp_id`, `emp_first_name`, `emp_last_name` and other columns.\n\nTo read people you write:\n\n`SELECT emp_id, emp_first_name, emp_last_name FROM employees;`\n\nThis says **what** you want (three columns from `employees`). It says nothing about files, blocks or how to loop. If the database changes how it stores the table, the statement stays the same. That is structural independence and the declarative style working together.\n\nThe older practice that the slide says ended: \"no more custom program per file\"."
}
```

#### `recap` (lesson `requirements-drive-database-choice`)
```json
{
 "id": "recap",
 "kind": "recap",
 "title": "Recap",
 "body": "- Requirements decide the database; relational is not the only answer.\n- Bank transfer: two steps (deduct, add), grouped into one transaction so no reader sees the middle.\n- Shopping cart: key = unique customer ID, value = list of items.\n- Principle: match the structure to what the task needs.\n- Next in the course: Codd's relational model (1970)."
}
```

## 3. Slides and the 8 primitives

Every slide: `{ "id", "title", "primitive", "spec", "ref", "provenance"? }`. Slide ids are unique within the lesson. `ref` is a valid ref: the unit the slide teaches, or for an authored slide the unit it extends. Any primitive outside this list is rejected (`E-PRIM`).

| `primitive` | `spec` | Limits | Use it for |
|---|---|---|---|
| `text` | `{body}` | body ≤ 1,500 characters | the opening idea, or the closing recap. Never more than 1–2 per lesson |
| `stepper` | `{steps: [{title, body}]}` | 2–10 steps | an ordered list, a procedure or an acronym, revealed one step at a time |
| `compare` | `{columns, rows, note?}` | 2–6 columns; 2–12 rows; each row = a label followed by exactly one cell per column | two or more things side by side (models, options, thresholds) |
| `flow` | `{nodes: [{id, label, sub?}], steps: [{title, body, active, arrows}]}` | 2–8 boxes; 2–10 steps; the ids in `active` and `arrows` must be box ids | a mechanism with moving parts: a request through replicas, a key to a shard |
| `timeline` | `{events: [{when, title, body}]}` | 3–12 events, in order | history, versions, the order of a process over time |
| `quorum` | `{replicas, intro}` | replicas 3–9 | a replication sandbox with R and W sliders: quorums, consistency against latency |
| `kvrepl` | `{intro, script: [{cmd, out, explain}], hint?}` | 3–20 commands | a terminal the learner types into or replays: commands and their output. Say in `intro` when the syntax is invented for the demo |
| `chooser` | `{intro, choices, cases: [{scenario, answer, why}]}` | 2–5 choices; 2–8 cases; `answer` = a choice index (0-based) | apply a rule: classify cases, pick the right model for a situation |

All visible strings are markdown-lite or plain text. A `compare` row like `["Lowest (1)", "fast", "risky"]` has a label plus one cell per column: with 2 columns that is 3 strings. Use `"-"` for an empty cell. The most common `E-PRIM` is a row with the wrong cell count.

Pick the primitive by what the content does, not for variety. A list of properties is a `stepper`, a trade-off is a `compare`, a mechanism is a `flow`, a decision is a `chooser`, a command set is a `kvrepl`. A sandbox you design (`quorum`, `kvrepl` with invented commands) is `"provenance": "authored"`, with honest wording in `intro`.

One real example of each:

#### `text` (lesson `requirements-drive-database-choice`)
```json
{
 "id": "s1",
 "title": "Data management is not just relational",
 "primitive": "text",
 "ref": "L1#6",
 "spec": {
  "body": "**The central idea:** data management is not synonymous with relational databases.\n\n- A **bank transfer** needs strict, all-or-nothing consistency.\n- A **shopping cart** needs speed; a simple key-value store suffices.\n\nRequirements decide the structure."
 }
}
```

#### `stepper` (lesson `acid-vs-base`)
```json
{
 "id": "sl-base-stepper",
 "title": "BASE, one letter at a time",
 "primitive": "stepper",
 "ref": "L3#11",
 "spec": {
  "steps": [
   {
    "title": "Basically Available",
    "body": "A partial failure is tolerated and the rest of the system keeps serving. Replicas mean queries still succeed if a server fails."
   },
   {
    "title": "Soft State",
    "body": "The state is not fixed. A value may be overwritten by more recent data later on."
   },
   {
    "title": "Eventually Consistent",
    "body": "Copies may differ briefly, then converge to the same value once replication catches up."
   }
  ]
 }
}
```

#### `compare` (lesson `quorum-and-replication-factor`)
```json
{
 "id": "s1-two-dials",
 "title": "Two dials: read and write thresholds",
 "primitive": "compare",
 "ref": "L3#9",
 "spec": {
  "columns": ["Read threshold", "Write threshold"],
  "note": "A quorum is the number of servers that must respond for a read or write to count as complete.",
  "rows": [
   ["Trades speed against", "Consistency", "Durability"],
   [
    "Lowest (1)",
    "With 5 replicas: fastest, but may return stale data",
    "Fast but risky: lose that server and the data is gone"
   ],
   [
    "Higher / recommended",
    "5 guarantees a consistent read but is slowest",
    "At least 2, with more replicas than the threshold, protects durability without slowing writes much"
   ],
   ["Middle value", "e.g. 3: servers agree by majority", "-"]
  ]
 }
}
```

#### `flow` (lesson `shard-key-selection`)
```json
{
 "id": "s4-cardinality-flow",
 "title": "Cardinality: a Yes/No key caps the shards",
 "primitive": "flow",
 "ref": "L2#26",
 "spec": {
  "nodes": [
   {"id": "yes", "label": "Value: Yes"},
   {"id": "no", "label": "Value: No"},
   {"id": "s1", "label": "Shard 1", "sub": "Jonas, Kevin"},
   {"id": "s2", "label": "Shard 2", "sub": "Vincent"}
  ],
  "steps": [
   {
    "title": "Only two values",
    "body": "A Yes/No key can only ever take two values.",
    "active": ["yes", "no"],
    "arrows": []
   },
   {
    "title": "At most two shards",
    "body": "Each value fills one shard, so two shards is the ceiling, and they rarely balance.",
    "active": ["yes", "no", "s1", "s2"],
    "arrows": [["yes", "s1"], ["no", "s2"]]
   },
   {
    "title": "The fix",
    "body": "Choose a high-cardinality key (many distinct values) so data divides evenly across shards.",
    "active": [],
    "arrows": []
   }
  ]
 }
}
```

#### `timeline` (lesson `codd-relational-model-1970`)
```json
{
 "id": "sl1",
 "title": "Where 1970 sits in the story",
 "primitive": "timeline",
 "ref": "L1#9",
 "provenance": "authored",
 "spec": {
  "events": [
   {
    "title": "A custom program per file",
    "when": "Before the relational model",
    "body": "The older practice the slide says ended: \"no more custom program per file\". Programs broke when storage changed."
   },
   {
    "title": "Codd publishes the relational model",
    "when": "1970",
    "body": "Built on relational algebra, a formal mathematical foundation."
   },
   {
    "title": "Structural independence and SQL",
    "when": "After the model",
    "body": "Logical organization is separated from physical storage, and one declarative language is shared across systems."
   },
   {
    "title": "Limits of the relational model",
    "when": "Later in Lecture 1",
    "body": "Schema first and ACID overhead motivate NoSQL, which stores JSON. Source: L1#19 (the limits), not L1#9."
   }
  ]
 }
}
```

#### `quorum` (lesson `quorum-and-replication-factor`)
```json
{
 "id": "s2-sandbox",
 "title": "Sandbox: set R and W with 5 replicas",
 "primitive": "quorum",
 "ref": "L3#9",
 "provenance": "authored",
 "spec": {
  "intro": "Set the read and write quorum sizes. Try R = 1 (fast, maybe stale), R = 5 (consistent, slowest), R = 3 (majority), and W = 1 against W = 2 or more. The overlap indicator (R + W greater than N) is an authored rule of thumb, not course content; the course frames W = 1 as a durability risk, not a staleness one.",
  "replicas": 5
 }
}
```

#### `kvrepl` (lesson `requirements-drive-database-choice`)
```json
{
 "id": "s3",
 "title": "The shopping cart as key to value",
 "primitive": "kvrepl",
 "ref": "L1#8",
 "provenance": "authored",
 "spec": {
  "intro": "Simulated key-value lookups for the cart example. The commands are our own generic pseudo-syntax, not a real product's; the data (customerID 4821 and its three items) is from the slide.",
  "hint": "Try: GET 4821",
  "script": [
   {
    "cmd": "GET 4821",
    "explain": "The key is the unique customer ID (4821); the value is the list of items in the cart.",
    "out": "[\"USB-C cable\", \"Laptop stand\", \"Notebook\"]"
   },
   {
    "cmd": "PUT 4821 [\"USB-C cable\", \"Laptop stand\", \"Notebook\", \"Pen\"]",
    "explain": "Adding an item just replaces the value stored under the same key.",
    "out": "OK"
   },
   {
    "cmd": "GET 4821",
    "explain": "One lookup by key returns the whole cart.",
    "out": "[\"USB-C cable\", \"Laptop stand\", \"Notebook\", \"Pen\"]"
   }
  ]
 }
}
```

#### `chooser` (lesson `codd-relational-model-1970`)
```json
{
 "id": "sl5",
 "title": "WHAT or HOW?",
 "primitive": "chooser",
 "ref": "L1#9",
 "provenance": "authored",
 "spec": {
  "intro": "Classify each statement by the way it talks to the data.",
  "cases": [
   {
    "answer": 0,
    "scenario": "SELECT emp_id, emp_first_name FROM employees;",
    "why": "SQL is declarative: it names the data wanted, not the steps to fetch it."
   },
   {
    "answer": 1,
    "scenario": "A custom program written for one file that walks through its records.",
    "why": "This is the older practice that the slide says ended: \"no more custom program per file\"."
   },
   {
    "answer": 2,
    "scenario": "The way blocks and indexes are laid out on disk changes, and existing programs keep working.",
    "why": "That is the physical side; structural independence keeps it separate from the logical organization."
   }
  ],
  "choices": ["States WHAT is wanted", "Describes HOW to fetch it", "Concerns physical storage"]
 }
}
```

## 4. Checkpoints

```json
{ "id": "cp1", "type": "mcq", "prompt": "...", "options": ["...", "..."], "answer": 1,
  "explanation": "...", "ref": "L3#10", "quote": "verbatim fragment", "trap": "optional: the classic mistake" }
```

| `type` | Fields | Rules |
|---|---|---|
| `mcq` | `options`, `answer` | 2–6 options; `answer` is a 0-based index |
| `multi` | `options`, `answers` | 3–8 options; `answers` = indices, at least 1. Say "Select all that apply" |
| `fill` | `accepted` | `prompt` contains `____` (four underscores) exactly once; `accepted` = 1–8 answers, with the usual variants ("500", "500 MB/s") |
| `short` | `modelAnswer`, `rubric` | `rubric` = 2–6 marking points (an array, or one string with one point per line) |

Every question has an `explanation`, a `ref` and a verbatim `quote` that supports the correct answer. Question ids are unique within the lesson.

Good questions:
- Each tests a key fact or a skill from the lesson. Spread them over the node's key facts, and aim the niche ones at numbers, names and exact wording.
- Distractors are the course's own neighbouring concepts and the classic confusions, never nonsense.
- The explanation says why the answer is right **and** why the tempting wrong answer is wrong. Use `trap` for the classic mistake.
- Mix the types: a core node gets at least one `fill`, `multi` or `short`.

Real questions:

#### `mcq` (lesson `redis-set-get-del-mset-mget`)
```json
{
 "id": "q3",
 "type": "mcq",
 "ref": "T3#12",
 "prompt": "In the key student:20231045:program, which part is the attribute?",
 "options": ["student", "20231045", "program", "Computer Science"],
 "answer": 2,
 "quote": "Identify the entity, the identifier and the attribute in the key student:20231045:program.",
 "explanation": "Entity = student, identifier = 20231045, attribute = program. \"Computer Science\" is the value, not part of the key."
}
```

#### `multi` (lesson `shard-key-selection`)
```json
{
 "id": "q2",
 "type": "multi",
 "ref": "L2#23",
 "prompt": "Which three properties of a shard key drive even distribution? Select all that apply.",
 "options": ["Monotonic change", "Frequency", "Cardinality", "Replication factor", "Consistency level"],
 "answers": [0, 1, 2],
 "quote": "Three properties of the key drive even distribution:",
 "explanation": "The course names monotonic change, frequency and cardinality. Replication factor and consistency level are not key properties."
}
```

#### `fill` (lesson `requirements-drive-database-choice`)
```json
{
 "id": "q2",
 "type": "fill",
 "ref": "L1#8",
 "prompt": "In the shopping cart example, the key is the unique ____.",
 "accepted": ["customer ID", "customerID", "customer id", "customer identifier"],
 "quote": "The key is the unique customer ID.",
 "explanation": "The key is the customer ID; the value is the list of items."
}
```

#### `short` (lesson `redis-set-get-del-mset-mget`)
```json
{
 "id": "q5",
 "type": "short",
 "ref": "T3#16",
 "prompt": "Why is the NX option useful when two portal servers register students at the same time?",
 "modelAnswer": "NX writes only if the key does not exist yet. The first server creates the key and the second one finds it already there and writes nothing, so it cannot overwrite the first server's data.",
 "rubric": "Says that NX means only-if-absent.\nSays that the second (concurrent) write does not replace the existing value.",
 "quote": "why is it useful when two portal servers register students at the same time?",
 "explanation": "The lab ties NX to protecting existing data when concurrent servers register students."
}
```

## 5. Traps

A trap is a place where learners lose marks: two terms the course distinguishes, a number that is easy to swap (250 against 500), a rule with an exception, a default that surprises, or a word that means something narrower in the course. Find them in the units ("not", "only", "unlike", "but", "warning", "common mistake") and in the contrasts between neighbouring nodes. Write each one in the trap section as `- Trap: <the mistake>. <the truth>, as L4#44 states.` Reuse the best ones as `trap` fields of questions and in the main guide's `traps` section.

## 6. The audit loop (L3)

After you write a lesson, switch roles: you are an examiner trying to prove the lesson wrong. Go through it item by item, against the units (`gxhelp show`):

1. **Refute.** For every fact, slide claim, cell, step, answer and explanation, ask: does the cited unit really say this? Is the number, name or direction right? Is an authored claim presented as course content? Is a distractor accidentally correct? Does a `compare` cell overstate the slide? Count every problem you find in `refuted`.
2. **Fix.** Correct each problem in the lesson: re-quote, re-word, mark it `"provenance": "authored"`, or delete the claim. Count the fixes in `fixed`.
3. **Record.** `"audit": {"by": "<model> self-audit", "refuted": N, "fixed": N, "at": "<UTC time>", "note": "<one line on what changed>"}`. Make `fixed` ≥ `refuted`. If you found nothing, write `"refuted": 0, "fixed": 0` and say in `note` what you checked.

Validate after the audit. An audit that finds nothing on a long lesson usually means it was not done: look again at numbers and at authored content.

## 7. Quick self-check before validating

- Section, slide and question counts are inside the bar for the node's priority, and the section order is right (`prereq` first when there are prerequisites, `recap` last).
- At least 2 interactive slides for a core node (1 otherwise), and every `compare` row has the right cell count.
- Every `fill` prompt has `____` exactly once. Every `answer` index exists. Every question has `explanation`, `ref` and `quote`.
- Every quote was copied from the unit (check doubtful ones with `gxhelp find`). A quote that runs over several lines of the unit joins them with one space, and keeps characters such as `…` exactly.
- Authored content is marked. There is no HTML or links in any string.
