# Exam profile and practice paper

The exam profile records what is **known** about the professor's exam. The practice paper is **your** paper, built from the course to rehearse the forms in the profile. Neither may invent facts about the real exam.

## 1. Intake questions

Ask these in the stage 0 message (numbered, all optional). Write down which answers the user actually gave.

1. **Type**: final, midterm, continuous assessment, oral, project defence, practical on a machine?
2. **Format**: open questions, MCQ, mixed, case study, exercises, code on paper?
3. **Duration and points**: how long is it, and how many points, if you know?
4. **Scope**: which lectures and TPs? Lessons only, or labs too? Anything excluded?
5. **Documents**: open book or closed? Calculator, cheat sheet?
6. **What the professor said**: themes announced, "there will be a question on X", "history matters", "know the commands".
7. **Past papers or sample questions**: attach them if you have them. They become sources (`P1`, role `past-paper`) and the strongest evidence for the forms.
8. **Time left**: how many hours can you study before the exam? (This sizes an `hours` or `exam` focus pathway.)

## 2. Confidence

Every profile and every form carries a `confidence`:

| Value | Use it when |
|---|---|
| `user-stated` | the learner told you (or the syllabus they gave says so) |
| `derived-from-artifact` | you read it in a past paper, sample questions or an official document in the sources |
| `inferred` | your own reading of the course (a lesson-only theory course probably has define-and-explain questions). Say why in `description` |

**Never invent durations or point totals.** If nobody stated it and no artifact shows it, the value is `null` and its field name goes in `unknownFields`. The same goes for `openBook`, `lessonOnly` and `examType`: `null` when unknown.

## 3. `exam/profiles.json`

```json
{ "profiles": [ {
  "subject": "NoSQL", "semester": "S7", "examType": "final", "lessonOnly": true, "durationMin": null, "openBook": null,
  "confidence": "user-stated",
  "forms": [
    { "id": "niche-fact", "name": "Niche fact recall", "description": "Exact terms, numbers, names and lists as worded in the lectures.", "confidence": "user-stated" },
    { "id": "scenario", "name": "Situation-based question", "description": "A situation is given; name and justify the right model or setting.", "confidence": "inferred" } ],
  "emphasis": ["Exact lecture wording for definitions and lists"],
  "notes": "The learner said: lesson-focused final, no lab content.",
  "unknownFields": ["durationMin", "openBook", "points"],
  "refineWith": ["a past paper", "the syllabus page on assessment"] } ] }
```

Use stable form ids. Pick from `niche-fact`, `recall`, `define-explain`, `history`, `scenario`, `compare`, `command`, `design`, `calculation` and `code`, or make a new slug when the exam has a form that none of these covers. `emphasis` holds the learner's and the professor's words, not yours.

## 4. `exam/mock.json`: the practice paper

```json
{ "profile": { "subject": "NoSQL", "confidence": "inferred",
               "notes": "PRACTICE PAPER, not the professor's exam. Duration unknown. Points are this paper's own scoring. Forms from the exam profile; questions from the lecture slides only." },
  "blueprint": { "durationMin": null, "totalPoints": 30,
                 "sections": [ { "id": "A", "title": "Niche facts", "form": "niche-fact", "count": 5, "points": 10 },
                               { "id": "B", "title": "Situations", "form": "scenario", "count": 4, "points": 20 } ] },
  "mock": { "questions": [ { "id": "Q01", "type": "fill", "form": "niche-fact", "points": 2,
      "prompt": "Snappy compresses at about 250 MB/s and decompresses at about ____ MB/s.", "accepted": ["500", "500 MB/s"],
      "explanation": "The slide gives 250 MB/s for compression and 500 MB/s for decompression.", "trap": "Swapping the two figures.",
      "ref": "L4#44", "quote": "about 250 MB/s compression and 500 MB/s decompression", "nodeIds": ["ram-first-writes-lru-compression"] } ] } }
```

Rules (the validator checks the arithmetic, `E-SCHEMA`):
- `profile.notes` starts with **"PRACTICE PAPER, not the professor's exam."** and says what is known and what is not.
- `blueprint.durationMin` is the stated duration (from the user or a past paper), otherwise `null`. `totalPoints` is the practice paper's own scoring: say so in `notes` unless it was stated.
- One blueprint section per form. The section `count`s add up to the number of questions, and the section `points` add up to `totalPoints`. Each section's form has exactly `count` questions, and the question `points` add up to `totalPoints` too. Points are multiples of 0.5.
- Questions follow the checkpoint rules (`references/lessons.md` §4), plus `form` (a form id of the profile), `points` and `nodeIds` (existing nodes). Every question has `explanation`, `ref` and a verbatim `quote`.
- Every form of the profile gets at least one question. Spread the questions across the main stages and favour core nodes. Respect the scope: no TP questions when the exam is lesson-only.
- With a past paper, mirror its structure: the same forms, similar weights and the same kinds of prompt, with `confidence: "derived-from-artifact"`. Never copy its questions as yours; rehearse the same skills on other content.
- Size: 12–25 questions for a module, about 5 for a single lecture; for a pathway course's final quiz, 10–30 across the steps.

## 5. In the main guide

The `checklist` section can point at the paper ("Do the practice paper under time if you know the duration"). The `traps` section reuses the paper's `trap` fields. Never state the real exam's format in the guide unless it is `user-stated` or `derived-from-artifact`.
