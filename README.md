# Personal LLM Skills & Workflows

This repository contains custom, modular behaviors and workflows that I've built for my own daily day-to-day interactions and projects with Claude and other agentic LLMs. 

These skills act as extended system instructions or workflows, turning conversational AI into powerful, structured workflow engines for research, design, development, and context management.

## Repository Structure

Each skill is self-contained in its own independent folder and includes its own `SKILL.md` along with any required references or assets. This structure is designed to be highly portable and accommodating to most AI tool architectures (like MCP servers, custom GPTs, Claude Projects, or autonomous agent environments).

```text
.
├── skills/
│   ├── aggregate-deep-research/
│   ├── app-idea-to-build-prompt/
│   ├── context-handoff/
│   ├── context-resume/
│   ├── external-delegation/
│   ├── ghosty-spec/
│   ├── project-uphaul/
│   ├── scenario-coverage-testing/
│   ├── subject-full-guide/
│   └── yt-deep-extraction/
├── claude-web-skills/
│   └── *.skill (packaged web skills)
└── README.md
```

## Available Skills

### 1. `ghosty-spec`
**Spec-Driven Development & Wave DAG Engine**
Injects the Ghosty Spec-Driven Development (SDD) workflow and a parallel execution engine natively into the workspace, using the exact on-disk spec format read and written by the Kiro IDE.
- **Kiro-Compatible Format:** Reads and writes `.kiro/specs/{feature}/` with `.config.kiro` metadata, EARS-formatted requirements, and Kiro's own checkbox/task-numbering conventions, so specs are interchangeable with the real Kiro app in both directions.
- **Documentation First:** Forces the creation of rigorous requirements, architectural designs, and task lists before execution, honoring `workflowType` (requirements-first or design-first) and `specType` (feature or bugfix).
- **Resumable Wave DAG Execution:** Parses tasks into dependency waves, dynamically schedules them across specialized agents in parallel, and writes progress back into `tasks.md` so a run can be closed and resumed exactly where it left off.
- **Quality & Trackability:** Trades immediate speed for deliberate correctness, allowing drafts to be reviewed and modified before code is written.
*Use this when starting complex, multi-step projects where code quality, architectural integrity, and strict traceability matter more than raw speed.*

### 2. `aggregate-deep-research`
**Multi-Phase Deep Research Pipeline**
A robust, model-agnostic pipeline for comprehensive research. It transforms a simple prompt or topic into a full-fidelity interactive HTML guide through a strict multi-phase process:
- **Capability Probe & Web Research:** Gathering 50-1000 sources.
- **Decomposition:** Breaking the topic down into isolated aspects.
- **Standalone Reports:** Generating specific reports with claim-source bindings and numbers ledgers to prevent hallucinations.
- **Synthesis:** Aggregating data into a master synthesis and a final interactive HTML lesson.
*Ideal for critical personal research or generating comprehensive educational materials.*

### 3. `app-idea-to-build-prompt`
**App Idea → Concept GUI → Build Prompt**
Guides the full workflow for turning a raw app or product idea into concrete artifacts.
- **Concept GUI:** Creates an interactive HTML/CSS/JS concept that you can click through.
- **Build Prompt:** Generates a comprehensive and structured prompt designed to be handed off to an autonomous coding agent (like Claude Code) for the actual build.
*Use this when pitching an idea to flesh out features, make UI/UX design choices, and prepare a solid spec before development starts.*

### 4. `context-handoff`
**Lossless Conversation Exporter**
Exports the current conversation context into a structured, lossless package.
- Creates a human-readable Markdown transcript and a canonical JSON record.
- Bundles any uploaded files or images into a zip.
*Perfect for long conversations hitting context limits, sharing context with team members, or migrating a session to a new AI workspace without starting from scratch.*

### 5. `context-resume`
**Context Loader & Resumer**
The receiving-end counterpart to `context-handoff`.
- Reads the handoff package (`handoff.json`, `handoff.md`, and zip archives).
- Rehydrates the AI's context with all prior decisions, constraints, and files so work can continue seamlessly.
*Triggered at the start of a new conversation by uploading the handoff package to pick up exactly where you left off.*

### 6. `external-delegation`
**Cross-Session AI Handoff Prompt Generator**
Crafts a self-contained delegation prompt for handing off work to another AI session on a different account or platform.
- Translates current context, decisions, and codebase state into an over-specified prompt.
- Ensures the receiving model has exactly what it needs to continue without assumptions.
*Use when you need another model to continue work but the session boundary erases context.*

### 7. `project-uphaul`
**Project Audit & Overhaul Pipeline**
Runs a full, dynamic audit-and-overhaul pipeline on a project or codebase you didn't build or aren't familiar with.
- **Sequences specialist skills:** Calls router, review, and autoresearch skills in a specific order.
- **Diagnosis & Execution:** Classifies the project, scopes what's wrong, checks with the user, and executes the fix on a branch.
- **Bundled Capabilities:** Built using the Meta Skill Router, Code Overhaul Skill, Autoresearch Skill, and ARA Rigor Reviewer.
*Trigger this when you inherit a messy project, want to audit code built by a weaker model, or need a structured quality review.*

### 8. `yt-deep-extraction`
**YouTube Channel Deep Research & Extraction**
Deeply and losslessly extracts everything from a YouTube channel, playlist, or video list.
- **Gathers metadata, full transcripts, visuals, chapters, and creator claims.**
- **Compiles per-video research files, a cross-referenced master report, and an interactive HTML lesson.**
- Model and runtime agnostic; operates with whatever tools the host agent has available.
*Use this whenever you want to learn from, archive, build a course from, or mine knowledge out of any YouTube channel or set of videos.*

### 9. `scenario-coverage-testing`
**Full-Coverage Scenario QA for Agentic-AI Projects**
A domain-agnostic testing methodology that simulates realistic end-to-end user journeys across an entire project instead of isolated feature checks, with continuous monitoring and fix-forward recovery on every failure.
- **Universal Pipeline:** Maps any real project onto a 10-stage skeleton (intake → agent generation → wait/poll → review/edit → validation → issue detection → fix cycle → re-validation → finalization → post-completion check), then instantiates it with the actual screens, commands, and tools of the specific system.
- **Continuous Monitoring:** Every step is a checkpoint — watch logs, console output, network responses, exit codes after each action rather than only when something visibly breaks, catching silent failures (swallowed exceptions, degraded fallbacks) before they cascade into someone else's bug three steps later.
- **Fix-Forward Protocol:** When something breaks, stop at the exact failure point, diagnose root cause, apply the smallest correct fix, verify in isolation, then resume the scenario from that step so the persona's journey stays continuous and realistic — never restart-and-hope, never silently skip a step.
- **Coverage Matrix & Personas:** Builds an exhaustive surface inventory (GUI screens, CLI commands, API endpoints, agent handoffs, background jobs), designs 5-6 diverse personas covering every cell of that matrix with different entry points, tool combinations, data scales, and failure injection points, ensuring "full coverage" is a deliverable not a hope.
- **Deliverables:** Coverage matrix filled in, bug log for every incident found (with reproduction steps if unfixable), and a plain-language verdict summary of what's solid, risky, or needs human decision.
*Use this when you want to stress test or "break" an app built with Claude Code/Codex/omp.sh/Antigravity CLI, prep something for shipping, or run full QA on any agentic-AI project.*

### 10. `subject-full-guide`
**Comprehensive Course & Document Study Guide Generator**
Produces a complete, structured, printable course revision guide from attached course documents or a specified subject, delivered as a self-contained LaTeX document ready for PDF compilation or Markdown.
- **Exhaustive Coverage:** Captures every chapter's definitions, theorems, formulas, algorithms, worked examples, and comparative tables without silently cutting or shrinking material.
- **Strict Grounding:** Faithfully transcribes facts, formulas, and terminology exactly as presented in the source documents, preventing hallucinations and approximations.
- **Exercise-Solving Strategies:** Analyzes TD/TP practical materials and generates generalized problem-solving strategies grouped by topic, rather than isolated solved problems.
- **Multi-Part Splitting:** Automatically partitions extensive course materials into clean, numbered multi-part guides when content exceeds single-output constraints.
- **Publication Ready:** Formats output with complete document structure, tables of contents, standardized mathematical notation, and artifact-completion signaling.
*Use this when you need a complete, exhaustive, printable course guide or revision handout from lecture notes, slides, or textbooks instead of a surface-level summary.*
## How to Use

This repository offers skills in two different formats depending on where you intend to use them:

### 1. Normal Skills (`skills/`)
These are uncompressed, raw directory structures containing the `SKILL.md` and any associated reference files. 
- **Use for:** Terminal-based or CLI harnesses like Claude Code, Hermes, OMP (`omp.sh`), Odysseus, or custom LangChain/Flowise workflows.
- **Why:** They are easily readable by humans, version-controllable, and natively executable by most local autonomous agent environments that scan a local `skills` directory.

### 2. Claude Web Skills (`claude-web-skills/`)
These are packaged `.skill` files (which are actually ZIP archives containing the raw skill directories). 
- **Use for:** The Claude.ai web interface (Claude Projects).
- **Why:** You can upload these `.skill` files directly as project knowledge base attachments, allowing the web version of Claude to read the internal structure and instructions seamlessly.

## Credits

The `project-uphaul` skill bundles and builds upon several fantastic open-source skills:
- **Meta Skill Router** — ananddtyagi/cc-marketplace (Anand Tyagi)
- **Code Overhaul Skill** — ehmo/code-overhaul-skill (Rasty Turek)
- **Autoresearch Skill** — ehmo/autoresearch-skill (Rasty Turek)
- **ARA Rigor Reviewer** — Orchestra-Research/AI-Research-SKILLs (Orchestra Research), originally from ARA-Labs/Agent-Native-Research-Artifact
