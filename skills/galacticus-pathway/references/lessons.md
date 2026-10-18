# Writing a step's lesson (L2, then L3)

Every step of an A-to-Z course gets `lessons/<stepId>.json`: a **guide** (read), a **presentation** (play), a **checkpoint** (prove it), and for L3 an **audit**. The format is `FORMAT.md` §4; the examples below are real, validated content from the dogfood course "Replication, quorums and consistency" (complete steps in `assets/examples/`).

## 1. Anatomy

```json
{ "nodeId": "read-write-quorums",
  "guide": { "index": ["What you need first", "What a quorum is", "..."],
             "sections": [ GuideSection, ... ],
             "needs":   [ { "nodeId": "replication-and-replicas", "why": "A quorum counts replicas." } ],
             "related": [ { "nodeId": "eventual-consistency-and-base", "why": "Next step: ..." } ] },
  "slides": [ Slide, ... ],
  "checkpoint": [ Question, ... ],
  "audit": { "by": "...", "refuted": 0, "fixed": 0, "at": "2026-10-18T10:30:00Z", "note": "..." } }
```

- `nodeId` = the file name without `.json` = an existing step id. `needs` and `related` point to existing steps; `needs` lists the earlier steps this one builds on (it drives the `prereq` section).
- `index` = the section titles in order (the reader shows it as the table of contents).
- Fill the bar of the step's priority (§9.2). For `core`: 5–9 sections, prereq first (when `needs` is not empty), recap last; 6–9 slides, 2+ not `text`; 4–5 questions, 1+ not `mcq`. Run `a2z.py bar <stepId>`: it also lists the card key facts the lesson does not teach yet. Every key fact of the card must appear in the guide or the slides.

## 2. Guide sections

`{ "id", "title", "kind", "body", "facts"?, "refs"?, "provenance"? }`. Kinds: `prereq | definition | summary | formula | technique | example | trap | recap | history | scenario | command`.

`body` is **markdown-lite** only: `**bold**`, `` `code` ``, lines starting with `- ` are list items, a blank line separates paragraphs, a bare ref like `L3#9` becomes a source chip. No HTML, links, images, headings or numbered lists (write `- ` items). Escape `"` inside JSON strings.

A typical sequence for a core step: `prereq` → `definition` → one or two `technique`/`summary` → `example` or `scenario` (the course's worked example) → `formula`/`command` when the course has one → `trap` → `recap`.

**prereq** names what is needed and why, and never re-teaches it:

```json
{
  "id": "prereq",
  "title": "What you need first",
  "kind": "prereq",
  "body": "- Step 1: a **replica** is one copy of the data; how many replicas to keep is the key parameter of replication.\n- Step 4: designers mostly trade **consistency against availability**, and the two-phase commit pays for consistency with speed.\n\nA quorum is the dial between those extremes.",
  "refs": [
    "L4#38",
    "L3#6",
    "L3#5"
  ]
}
```

**A section with facts.** The body explains in your words; `facts` hold the course statements, each with its verbatim quote. Put every number of the slide in a fact:

```json
{
  "id": "read-threshold",
  "title": "The read threshold",
  "kind": "technique",
  "body": "The read threshold trades **response time against consistency**. With **5 replicas** (L3#9):\n\n- **Threshold 1**: fastest, but may return stale data.\n- **Threshold 5**: guarantees a consistent read, but is slowest.\n- **A middle value (e.g. 3)**: lets the servers agree by majority.\n\nThe lecture 4 example adds: a higher read quorum gives fresher data, at the cost of higher latency (L4#39).",
  "facts": [
    {
      "text": "The read threshold trades response time against consistency.",
      "ref": "L3#9",
      "quote": "Read threshold → response vs. consistency"
    },
    {
      "text": "With 5 replicas, a read threshold of 1 is fastest but may return stale data.",
      "ref": "L3#9",
      "quote": "threshold 1 is fastest but may return stale data"
    },
    {
      "text": "With 5 replicas, a read threshold of 5 guarantees a consistent read but is slowest.",
      "ref": "L3#9",
      "quote": "threshold 5 guarantees a consistent read but is slowest"
    },
    {
      "text": "A middle value such as 3 lets servers agree by majority.",
      "ref": "L3#9",
      "quote": "A middle value (e.g., 3) lets servers agree by majority"
    },
    {
      "text": "A higher read quorum gives fresher data at the cost of higher latency.",
      "ref": "L4#39",
      "quote": "A higher read quorum gives fresher data, at the cost of higher latency."
    }
  ],
  "refs": [
    "L3#9",
    "L4#39"
  ]
}
```

**trap**: one `- Trap: ...` line per classic confusion, each pointing to the unit that settles it:

```json
{
  "id": "traps",
  "title": "Traps",
  "kind": "trap",
  "body": "- Trap: the read dial is about **consistency** (stale data); the write dial is about **durability** (losing data). Do not swap them (L3#9).\n- Trap: the quorum is not the number of replicas. The number of replicas is how many copies exist (L4#38); the quorum is how many of them must answer.\n- Trap: the slide guarantees a consistent read only for threshold 5 of 5. Threshold 3 is described as servers agreeing **by majority** (L3#9).\n- Trap: `R + W > N` is our authored rule, not a course statement; quote the slides when you are asked what the course says.",
  "refs": [
    "L3#9",
    "L4#38"
  ]
}
```

**Authored content.** A rule the course never states, an analogy, a worked number you chose: a whole section or slide with `"provenance": "authored"`, or an inline label ("our example", "our reading", "our wording") inside an otherwise sourced section. The reader shows an "Authored explanation, not from the course" badge on authored slides.

```json
{
  "id": "overlap",
  "title": "When does a read see the latest write?",
  "kind": "formula",
  "provenance": "authored",
  "body": "This rule is **not on the slides**; it is the standard way to reason about the course's examples.\n\nWith `N` replicas, a write quorum `W` and a read quorum `R`:\n\n`R + W > N`\n\nmeans every read quorum overlaps every write quorum, so at least one replica in each read holds the latest acknowledged write.\n\n- L4#39: `N = 3, W = 2, R = 2` gives `4 > 3`: the read reaches a fresh replica (as in the example, where two replicas answer v2).\n- `N = 3, W = 2, R = 1` gives `3`, not more than 3: a read may hit replica 3 alone and get v1.\n- L3#9: `N = 5` with `R = 5` overlaps any `W >= 1`, which is why threshold 5 guarantees a consistent read.",
  "refs": [
    "L4#39",
    "L3#9"
  ]
}
```

`recap` is 3–6 list items, one per idea of the step, no new facts.

## 3. Facts and quotes

`{ "text": "your sentence", "ref": "L3#9", "quote": "verbatim fragment" }`

- Copy the quote from `a2z.py show` output, never from memory. 8–240 characters, 12–140 is best. You may cut mid-sentence; keep the slide's own spelling, typos and symbols (`·`, `|`, `→`, `$1,000`).
- What the matcher forgives (FORMAT.md §3.6): curly versus straight quotes, dashes, `→` versus `->`, accents, case and any run of whitespace (so a quote can span the line breaks of a slide). Nothing else.
- A quote must sit inside **one unit**: title, text, notes and table cells of that unit are searched together (table cells are joined with spaces).
- The same quote may support several facts. A fact's `text` may be shorter or clearer than the quote but must say only what the quote supports.
- Check doubtful quotes with `a2z.py find "<quote>"`; `gxformat.py validate` checks all of them.

## 4. Slides and the eight primitives

Every slide: `{ "id", "title", "primitive", "spec", "ref", "provenance"? }`. `ref` is the unit the slide teaches (for an authored slide, the unit it extends). Ids are unique in the lesson.

**Pick the primitive by the shape of the idea:**

| The idea is... | Use | Not |
|---|---|---|
| a sequence the learner must hold in order (phases, lab tasks, a failure drill) | `stepper` | a long `text` list |
| a system with parts that talk to each other (who sends what to whom) | `flow` | a static picture in words |
| two to six options judged on the same criteria | `compare` | two separate text slides |
| events in time, or "before / during / after" states | `timeline` | a stepper without times |
| replication thresholds (R, W, N) | `quorum` | numbers in prose |
| commands, a protocol or a calculation the learner can replay | `kvrepl` | code in a text slide |
| a decision or classification the learner must make | `chooser` | a rhetorical question |
| an explanation that has no moving parts | `text` | (keep these few) |

**text**: `{ "body": "markdown-lite" }`, at most 1,500 characters.

```json
{
  "id": "s1-what",
  "title": "Servers vote",
  "primitive": "text",
  "ref": "L3#9",
  "spec": {
    "body": "A **quorum** is the number of servers that must respond for a read or write to count as complete. Servers effectively \"vote\" on the answer.\n\nTwo dials, set separately:\n\n- **Read threshold**: response against consistency.\n- **Write threshold**: response against durability. L3#9"
  }
}
```

**stepper**: `{ "steps": [ { "title", "body" } ] }`, 2–10 steps, revealed one at a time.

```json
{
  "id": "s3-failure",
  "title": "Ring: surviving a node failure",
  "primitive": "stepper",
  "ref": "L4#37",
  "spec": {
    "steps": [
      {
        "title": "1. Copies on the neighbours",
        "body": "Data written to S4 is also written to S3 and S5."
      },
      {
        "title": "2. S4 goes down",
        "body": "S3 and S5 answer read requests for S4's data."
      },
      {
        "title": "3. Writes keep coming",
        "body": "They also accept writes destined for S4."
      },
      {
        "title": "4. S4 comes back",
        "body": "S3 and S5 send it the writes it missed. No master was ever involved."
      }
    ]
  }
}
```

**compare**: `{ "columns": [...], "rows": [ [label, cell per column...] ], "note"? }`, 2–6 columns, 2–12 rows, each row = a label followed by exactly one cell per column. Use `note` to say which rows are the course and which are yours.

```json
{
  "id": "s1-acid-base",
  "title": "ACID versus BASE",
  "primitive": "compare",
  "ref": "L3#10",
  "spec": {
    "columns": [
      "ACID",
      "BASE"
    ],
    "rows": [
      [
        "Family",
        "The relational model",
        "Common to NoSQL"
      ],
      [
        "Guarantees",
        "Strong, strict guarantees on every transaction, correctness first",
        "Looser guarantees that favor availability and speed at scale"
      ],
      [
        "Letters",
        "Atomicity, Consistency, Isolation, Durability",
        "Basically Available, Soft State, Eventually Consistent"
      ]
    ]
  }
}
```

**flow**: `{ "nodes": [ { "id", "label", "sub"? } ], "steps": [ { "title", "body", "active": [ids], "arrows": [[from, to]] } ] }`, 2–8 boxes, 2–10 steps; every id in `active` and `arrows` is a box id. Each step lights the boxes involved and draws the messages of that moment.

```json
{
  "id": "s3-write",
  "title": "Write: 3 replicas, wait for 2",
  "primitive": "flow",
  "ref": "L4#39",
  "spec": {
    "nodes": [
      {
        "id": "app",
        "label": "Application",
        "sub": "writes v2"
      },
      {
        "id": "r1",
        "label": "Replica 1",
        "sub": "ack"
      },
      {
        "id": "r2",
        "label": "Replica 2",
        "sub": "ack"
      },
      {
        "id": "r3",
        "label": "Replica 3",
        "sub": "background"
      }
    ],
    "steps": [
      {
        "title": "Send the write",
        "body": "The write of v2 goes to the 3 replicas.",
        "active": [
          "app",
          "r1",
          "r2",
          "r3"
        ],
        "arrows": [
          [
            "app",
            "r1"
          ],
          [
            "app",
            "r2"
          ],
          [
            "app",
            "r3"
          ]
        ]
      },
      {
        "title": "Two acks",
        "body": "Replica 1 written: ack. Replica 2 written: ack. Success is returned after 2 acks and the app moves on.",
        "active": [
          "r1",
          "r2",
          "app"
        ],
        "arrows": [
          [
            "r1",
            "app"
          ],
          [
            "r2",
            "app"
          ]
        ]
      },
      {
        "title": "The third in the background",
        "body": "Replica 3 is written in the background. Until it is, it still holds v1.",
        "active": [
          "r3"
        ],
        "arrows": []
      }
    ]
  }
}
```

**timeline**: `{ "events": [ { "when", "title", "body" } ] }`, 3–12 events in order. `when` may be a date, a time or a relative label (`t0`, `t0 to t1`); if the times are yours, mark the slide authored.

```json
{
  "id": "s2-address",
  "title": "The address update, replica by replica",
  "primitive": "timeline",
  "ref": "L3#11",
  "provenance": "authored",
  "spec": {
    "events": [
      {
        "when": "t0",
        "title": "The write",
        "body": "A user updates her address on one server."
      },
      {
        "when": "t0, instantly",
        "title": "Nearby replica",
        "body": "A nearby replica updates instantly."
      },
      {
        "when": "t0 to t1",
        "title": "Copies disagree",
        "body": "A data center thousands of miles away lags: briefly, the copies disagree. A reader there may see the old address."
      },
      {
        "when": "t1",
        "title": "Converged",
        "body": "Replication catches up and every copy holds the new address: eventually consistent."
      }
    ]
  }
}
```

**quorum**: `{ "replicas": 3..9, "intro": "..." }`: a sandbox with R and W sliders, live staleness and overlap. The `intro` tells the learner which settings to try and what to notice; use the course's own numbers.

```json
{
  "id": "s2-sandbox",
  "title": "Quorum sandbox: 5 replicas",
  "primitive": "quorum",
  "ref": "L3#9",
  "provenance": "authored",
  "spec": {
    "replicas": 5,
    "intro": "This is the slide's own set-up: 5 replicas. Set R = 1 and watch reads get fast but possibly stale; set R = 5 for a guaranteed consistent but slowest read; try R = 3, the majority value. Then set W = 1 and imagine losing that one server: the data is gone. W = 2 or more protects durability. Our extra rule to test: whenever R + W is greater than 5, every read overlaps the latest write."
  }
}
```

**kvrepl**: `{ "intro", "script": [ { "cmd", "out", "explain" } ], "hint"? }`, 3–20 commands; the learner types them or replays them. Say in `intro` when the syntax is invented, and when outputs are written by you rather than captured. Real lab commands are best (the master-slave step replays the Redis lab's own `MSET`, `INCR`, `MGET` and `INFO replication`).

```json
{
  "id": "s4-terminal",
  "title": "Terminal: commit, fail, roll back",
  "primitive": "kvrepl",
  "ref": "L3#5",
  "provenance": "authored",
  "spec": {
    "intro": "The command syntax is invented for this demo. The behaviour follows L3#5: write to the primary, then the backup; commit only if both succeed, otherwise roll back.",
    "script": [
      {
        "cmd": "write balance 900 --2pc",
        "out": "phase 1: primary committed\nphase 2: backup committed\nDONE: transaction commits",
        "explain": "Both writes succeed, so the transaction commits and both servers hold 900."
      },
      {
        "cmd": "write balance 800 --2pc --fail backup",
        "out": "phase 1: primary committed\nphase 2: backup FAILED\nROLLBACK: the whole transaction is undone",
        "explain": "If either write fails, the whole transaction rolls back."
      },
      {
        "cmd": "read balance --from primary",
        "out": "900",
        "explain": "The primary is back to 900: the two servers stay consistent."
      },
      {
        "cmd": "read balance --from backup",
        "out": "900",
        "explain": "Same value on the backup, so it can take over if the primary fails."
      }
    ],
    "hint": "Start with: write balance 900 --2pc"
  }
}
```

**chooser**: `{ "intro", "choices": [2–5], "cases": [ { "scenario", "answer": index, "why" } ] }`, 2–8 cases. Mix the course's own cases with yours and say which is which in `intro`.

```json
{
  "id": "s5-pick-two",
  "title": "CA, CP or AP?",
  "primitive": "chooser",
  "ref": "L3#6",
  "provenance": "authored",
  "spec": {
    "intro": "The first three cases restate L3#6. The last two come from the ride-hailing exercise L3#8, which has no answer key: the answers are our reading.",
    "choices": [
      "CA",
      "CP",
      "AP"
    ],
    "cases": [
      {
        "scenario": "A primary and a backup kept identical with a two-phase commit, assuming the network never splits.",
        "answer": 0,
        "why": "CA: consistent and available, assumes no partition (two-phase commit)."
      },
      {
        "scenario": "During a network split, the system refuses some queries rather than risk different answers on each side.",
        "answer": 1,
        "why": "CP: consistent and partition-tolerant, blocks some queries, so availability suffers."
      },
      {
        "scenario": "A shopping cart that always answers, even if a copy is a little behind.",
        "answer": 2,
        "why": "AP: available and partition-tolerant, may return stale data (the cart)."
      },
      {
        "scenario": "Ride-hailing during a 90-second split: the surge-price display.",
        "answer": 2,
        "why": "It tolerates small staleness, so stay available."
      },
      {
        "scenario": "Ride-hailing during a 90-second split: the payment step, which must never double-charge.",
        "answer": 1,
        "why": "Correctness wins: block the charge rather than risk two replicas charging."
      }
    ]
  }
}
```

## 5. Checkpoint questions

Every question: `id` (unique in the lesson), `type`, `prompt`, `explanation`, `ref`, verbatim `quote`, optional `trap` (the classic mistake).

| `type` | Fields |
|---|---|
| `mcq` | `options` (2–6), `answer` (index) |
| `multi` | `options` (3–8), `answers` (indices, at least 1) |
| `fill` | `prompt` contains `____` exactly once; `accepted` (1–8 answers: spellings, singular/plural, digits and words) |
| `short` | `modelAnswer`; `rubric` = 2–6 marking points |

```json
{
  "id": "cp1",
  "type": "mcq",
  "prompt": "What is a quorum?",
  "options": [
    "The number of replicas the cluster keeps",
    "The number of servers that must respond for a read or write to count as complete",
    "The server that coordinates a two-phase commit",
    "The fastest replica"
  ],
  "answer": 1,
  "explanation": "A quorum counts responding servers; the number of copies kept is the replication parameter of step 1.",
  "ref": "L3#9",
  "quote": "the number of servers that must respond for a read or write to count as complete",
  "trap": "Confusing the quorum with the number of replicas."
}
```

```json
{
  "id": "cp3",
  "type": "multi",
  "prompt": "In the L4#39 example (3 replicas, wait for 2), which statements are true?",
  "options": [
    "Success is returned after 2 acks and the app moves on",
    "Replica 3 is written in the background",
    "A two-phase commit makes all three replicas agree before success",
    "On the read, two replicas agree on v2 and v2 is returned",
    "The app waits for all three acks"
  ],
  "answers": [
    0,
    1,
    3
  ],
  "explanation": "The example waits for 2 of 3 on both sides and explicitly has no two-phase commit, so replica 3 can briefly hold v1.",
  "ref": "L4#39",
  "quote": "Success returned after 2 acks; the app moves on."
}
```

```json
{
  "id": "cp2",
  "type": "fill",
  "prompt": "With 5 replicas, a read threshold of ____ guarantees a consistent read but is slowest.",
  "accepted": [
    "5",
    "five"
  ],
  "explanation": "Every replica must answer, so the read sees the current value; it waits for the slowest server.",
  "ref": "L3#9",
  "quote": "threshold 5 guarantees a consistent read but is slowest"
}
```

```json
{
  "id": "cp5",
  "type": "short",
  "prompt": "Why set the write threshold to at least 2 rather than 1?",
  "modelAnswer": "With a write threshold of 1 the write is fast but risky: only one server is sure to hold it, so if that server is lost the data is gone. Setting it to at least 2, with more replicas than the threshold, means the write is on two servers before success is returned, which protects durability without slowing writes much.",
  "rubric": [
    "Threshold 1: if that one server is lost, the data is gone",
    "At least 2 means the write is on two servers before success",
    "This protects durability",
    "It does not slow writes much (with more replicas than the threshold)"
  ],
  "explanation": "L3#9: the write dial is about durability.",
  "ref": "L3#9",
  "quote": "Setting it to at least 2 (with more replicas than the threshold)"
}
```

Write wrong options from neighbouring ideas (the other dial, the other model), never absurd ones. A `short` rubric lists what a full answer must contain, one point per idea.

## 6. The audit loop (L3)

After writing a lesson, change roles: you are now a strict examiner who wants to prove the lesson wrong.

1. **Refute.** Re-read every unit the lesson cites (`a2z.py show`) and check, item by item:
   - each fact's `text` says no more than its quote; each number, name and port matches the unit;
   - every slide and section statement without a quote is either supported by a cited unit or labelled authored;
   - answer keys: the right option is right, the wrong ones are wrong, `accepted` covers the reasonable spellings, rubrics match the model answer;
   - arithmetic and worked examples you made;
   - nothing presents your answer to an exercise as the course's answer;
   - every card key fact is taught (`a2z.py bar`).
2. **Fix** each failure in place, then validate.
3. **Record** it honestly in `audit`: `by` names the model and says whether it was a self-audit; `refuted` = what you found, `fixed` = what you fixed (`fixed` ≥ `refuted`); `note` says what the problems were. If you found nothing, write 0 and say what you checked. Never pad the counts.

```json
{
  "audit": {
    "by": "claude-opus-5-5 self-audit (the authoring model, in a separate refute pass; not an independent reviewer)",
    "refuted": 3,
    "fixed": 3,
    "at": "2026-10-18T10:30:00Z",
    "note": "Refuted: a compare cell inverted the L5#16 review answer and showed it as course content; \"replica\" was defined in non-authored text (guide and slide) although no slide defines it. Fixed: cell replaced by \"Not stated on the slides\"; both definitions labelled as our wording. All quotes machine-checked by gxformat validate."
  }
}
```
