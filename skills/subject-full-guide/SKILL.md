---
name: subject-full-guide
description: Writes the "Full Guide" - one complete, structured, printable course guide covering everything in the student's attached documents (every chapter's definitions, formulas, theorems, procedures and key facts, plus exercise-solving strategies for TD/TP), delivered as a LaTeX block that the app compiles to PDF. Use whenever the student clicks or asks for "Full Guide", a complete or full study guide, a full course handout, a revision guide, or "everything I need to know" from their documents - even if they never say "LaTeX" or "PDF". Do not use for a short summary, cheat sheet, flashcards, quiz or mind map; those have their own skills.
---

# Full Guide

A Full Guide is the document a student could revise from *instead of* the originals. It is longer and more complete than a Summarize result, organised like a real course handout, and printable. Its value is completeness plus accuracy: a missing chapter leaves a hole the student will not notice, and an invented fact will be learned as true. Both matter more than polish.

A Full Guide request is a request for a finished document, not problem-solving. Produce it completely even when Tutor mode is on; do not turn it into Socratic questioning.

## Workflow

1. **Read everything first.** Read every attached document front to back, noting page or slide numbers. In the study app, list the documents, then read each one (the same `list_documents` / `read_document` tools the sibling `nstudy-*` skills use); elsewhere, read the uploaded files. Never write the guide from the opening pages only.
2. **Fix the structure.** Follow the documents' own order and chapter titles. One `\section` per chapter or part. With several documents, give each its own part; if they clearly overlap, merge by topic and say so in one line under the title. Note whether a document is a TD/TP (contains exercises or practical tasks).
3. **Write each section** with only the subsections the material actually supports:
   - an overview of 2-3 sentences;
   - **definitions** (use `quote`), stated as the document states them;
   - **theorems and formulas** in math mode, with their conditions;
   - **procedures and algorithms** as a numbered `enumerate`, steps in the document's order;
   - **worked examples** the document itself gives, reduced to the method;
   - a real `tabular` whenever the document compares items or lists tabular data.
   Include every key concept, definition, formula, theorem, name, date and number that appears. Do not pad; drop repetition, not content.
4. **TD/TP closing section.** If any document contains exercises, end with `\section{Exercise-Solving Strategies}`: group strategies by topic or problem type; for each, give a name, step-by-step instructions, and the conditions under which it applies. Write them generally enough to reuse on similar exercises, not tied to the document's numbers. Give strategies, never the solved exercises.
5. **Optional quick reference.** When the material has many formulas or terms, finish with a short `\section{Quick Reference}` (a table of formulas or key terms collected from the sections above).
6. **Run the final check** below before sending.

## Rules

- **Ground everything in the documents.** Use only what they contain. If something is not in them, leave it out rather than guess. When outside knowledge is genuinely needed to make a point clear, mark it as such (`\textit{Beyond the documents: ...}`) and keep it rare. Say "the document does not specify..." instead of filling a gap with something plausible.
- **Copy facts exactly.** Numbers, formulas, names and dates are transcribed, never rounded or approximated. Use the field's precise standard terms.
- **Plain tone.** State facts the way the document states them. No self-justifying register ("this is evidenced by..."), no filler opener ("Here is your guide"), no filler closer.
- **Language.** Write in the language of the source documents (the student's language if there is no document), including section titles and the table of contents. If the app has a fixed output language, write in that language, translate technical terms to their standard equivalent, and keep the original term with a short gloss when none exists. Match natural idiom, number and date formats.
- **Citations.** Give page references as plain text, e.g. `(p. 12)`, or `(Doc title, p. 12)` with several documents. Keep chat-style citation markers and `\cite` out of the LaTeX block: `\cite` is stripped by the renderer and the marker syntax belongs to chat prose.

## Output format

Emit exactly one fenced block labelled `latex` containing a complete file, from `\documentclass{article}` to `\end{document}`. Rules the app enforces:

- Put `[ARTIFACT_COMPLETE]` on its own line immediately after the closing fence. It makes the "Generate PDF" button appear at the right moment and is stripped before display. Never put it on the fence line and never nest the block in another code block.
- At most one short sentence before the block. After the marker, at most a one-line offer (for example, to produce a cheat sheet or flashcards next).
- Structure: `\title \author \date \maketitle \tableofcontents`, then `\section \subsection \subsubsection \paragraph` (starred forms work and still appear in the contents). Use `\newpage` before each major part.
- Text: `\textbf \textit \emph \underline \texttt`; size switches take an argument, e.g. `\large{...}`.
- Lists and tables: `itemize` / `enumerate` (nestable), `tabular` with `&`, `\\` and `\hline` (or `\toprule \midrule \bottomrule`). Always a real table for tabular data, never dashes or pipes.
- Math: `$...$`, `\[...\]`, `equation` / `align` / `gather`; `\frac \sqrt`, Greek letters, `\leq \neq \to \in \sum \int`, `\gcd \log \max \sin`, `\bmod \pmod{n}`.
- Other: `quote` / `quotation`; `verbatim` for code or exact whitespace.
- Avoid `\cite \ref \includegraphics`, `figure`, `\newcommand` and custom macros: they are stripped with a notice. `\usepackage \geometry \hypersetup \pagestyle` are accepted and ignored, so skip them.

Skeleton to adapt:

```latex
\documentclass{article}
\title{Algorithms - Full Guide}
\author{Course documents}
\date{}
\begin{document}
\maketitle
\tableofcontents
\newpage
\section{Chapter 1 - Graph Traversal}
Two traversals visit every vertex of a graph: breadth-first and depth-first (p. 3).
\subsection{Definitions}
\begin{quote}
\textbf{Breadth-first search (BFS).} Visits vertices in order of distance from the source (p. 4).
\end{quote}
\subsection{Formulas}
On an adjacency list, BFS runs in $O(V + E)$ (p. 5).
\subsection{Procedure}
\begin{enumerate}
\item Enqueue the source and mark it visited.
\item Dequeue a vertex and visit it.
\item Enqueue each unvisited neighbour, marking it visited.
\item Repeat until the queue is empty.
\end{enumerate}
\newpage
\section{Exercise-Solving Strategies}
\subsection{Trace a traversal}
Draw the queue (or stack) after every step; apply when an exercise asks for a visiting order.
\end{document}
```
[ARTIFACT_COMPLETE]

## Very long material

Never shrink or silently cut chapters to fit. If the guide cannot fit in one response, split by chapters into parts. Each part is a complete, valid LaTeX file titled "... - Part k of N". Say which chapters each part covers, deliver part 1, and continue with the next part when the student asks.

## No document attached

If the student names a topic, write the guide from reliable knowledge (and search results, if a search tool is available). State in one line under the title that it comes from general knowledge, not from their course, and say plainly where you are unsure rather than guessing. If there is neither a document nor a topic, ask which topic they want or suggest attaching a document, using a single ` ```question ` block as the very last thing in the reply (2-5 short, concrete options, `"allowFreeText": true`).

## Outside the study app

Where there is no LaTeX-to-PDF renderer, keep the same structure and rules but write the guide as Markdown (headings, tables, `$math$`). If the student wants a file, build a Word or PDF document with the matching skill.

## Final check

- Every chapter or section of every document is represented.
- Every number, formula, name and date was re-checked against the source.
- Subsections exist only where the material supports them; nothing invented.
- TD/TP present: the strategies section exists and contains strategies, not solved exercises.
- The block runs from `\documentclass` to `\end{document}`, every environment is closed, no stripped macros are used.
- `[ARTIFACT_COMPLETE]` follows the closing fence, and the whole guide is in one language.

<!-- Provenance: reconstructed from prompts.json (assistant.summarize, assistant.summarizeTdTpAddendum, assistant.artifactAddendum, note.artifactAddendum, accuracyStandardsAddendum, citationAddendum, languageAdaptiveAddendum / languageFixedAddendum, tutorAddendum bypass list, questionBlockAddendum). The original QUICK_ACTIONS "Full Guide" prompt text (src/lib/quickActions.ts) was not in the uploaded files; if you find it, diff it against this skill. -->
