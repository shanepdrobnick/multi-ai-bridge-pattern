# The Multi-AI Bridge Pattern
### A coordination pattern for bridging creative AI and IDE AI in software development

**Invented by Shane Drobnick — March 2026**
Licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — free to use, attribution required.

> If you use this pattern in your work, a credit to Shane Drobnick with a link to this repository is required under the licence terms.

---

## The Problem

Modern AI development tools fall into two categories that don't talk to each other:

**Creative/Architectural AI** (e.g. Claude) — strong at system design, complex problem solving, novel approaches, pushing back on bad ideas, understanding context across an entire project. Weak at direct file access and mechanical implementation.

**IDE AI** (e.g. Cursor, Copilot) — strong at fast in-file implementation, boilerplate, refactoring, syntax recall. Weak at creative judgment, architectural thinking, and anything that requires understanding the whole system rather than the current file.

The result is engineers bouncing between tools with no coordination layer — manually translating between a design conversation and an implementation task, burning tokens on both sides, and losing fidelity every time.

**There's also a token problem.** Creative AI sessions are expensive and finite. You don't want to spend senior engineer tokens on boilerplate. You don't want to spend ten IDE AI iterations getting to something the senior engineer could have specified in one message.

---

## The Solution

A **bidirectional JSON bridge** between the two AI types, plus a **project sync tool** that gives the creative AI instant context at the start of every session.

```
┌─────────────────┐         ai_instructions.json        ┌─────────────────┐
│                 │  ─────────────────────────────────►  │                 │
│   Creative AI   │                                      │     IDE AI      │
│   (Senior Dev)  │  ◄─────────────────────────────────  │  (Junior Dev)   │
│                 │         project_sync.py output       │                 │
└─────────────────┘                                      └─────────────────┘
```

**`ai_instructions.json`** — Written by the creative AI. Read by the IDE AI. Contains:
- Exact task specifications with step-by-step implementation logic
- Architectural conventions and rules
- Known breaking changes and gotchas
- Design decisions that are final and must not be deviated from
- A prioritised task queue with status tracking

**`project_sync.py`** — Run by the developer at the start of each session. Output pasted to the creative AI. Provides:
- Full file inventory with line counts
- Complete class and function structure (without source code)
- JSON data file contents summary
- Files changed since last session
- Syntax error detection

---

## The Mental Model

Think of it as a **senior engineer / junior engineer** relationship:

| Role | Tool | Responsibilities |
|------|------|-----------------|
| Senior Engineer | Creative AI | Architecture, complex systems, design decisions, writing the spec, knowing when to push back |
| Junior Engineer | IDE AI | Implementing the spec, boilerplate, refactoring, mechanical execution |
| Technical Director | Developer | Creative vision, final decisions, directing both, knowing which tool fits which problem |

The senior engineer writes `ai_instructions.json`. The junior engineer reads it and implements exactly as specified. The developer runs `project_sync.py` to keep the senior engineer in context.

---

## Why This Works

**Token efficiency.** Creative AI tokens are spent on architecture and specification — high-value work. IDE AI tokens are spent on implementation — exactly what they're optimised for. No waste on either side.

**No translation overhead.** The developer doesn't manually translate between a design conversation and an implementation prompt. The spec file IS the prompt, written in a format the IDE AI can consume directly.

**Preserved context.** The creative AI loses context between sessions. `project_sync.py` restores full project understanding in one paste — file structure, architecture, what changed — without pasting entire source files.

**Clear ownership.** `ai_instructions.json` explicitly marks which decisions are final, which files not to touch, and who owns each problem. Junior AI cannot accidentally overwrite senior AI decisions.

**Compounding quality.** The creative AI's architectural judgment shapes every task the IDE AI implements. The result is mechanically competent code that's also architecturally sound — which is rare when using either tool alone.

---

## File Structure

```
your-project/
├── ai_instructions.json    # Claude writes this. Cursor reads this.
├── project_sync.py         # Run at session start. Paste output to Claude.
├── .sync_state.json        # Auto-generated. Tracks file changes between sessions.
└── ... your project files
```

---

## ai_instructions.json Structure

```json
{
  "_meta":          { "written_by", "read_by", "purpose" },
  "_conventions":   { "breaking changes", "style rules", "patterns to follow" },
  "_architecture":  { "module map", "startup sequence", "do not touch list" },
  "tasks": {
    "TASK_001": {
      "status":       "pending | in_progress | done",
      "priority":     "high | medium | low",
      "assigned_to":  "cursor | claude | developer",
      "description":  "plain English description",
      "files_to_edit": ["list of files"],
      "exact_change": { "precise implementation instructions" },
      "test":         "how to verify it worked",
      "do_not":       "explicit constraints"
    }
  },
  "known_issues":       { "open bugs with assigned owners" },
  "design_decisions":   { "final decisions — do not deviate without discussion" }
}
```

---

## project_sync.py Usage

```bash
# Start of session — paste full output to Claude
python3 project_sync.py

# Mid-session — see what Cursor changed
python3 project_sync.py --diff

# Quick sanity check after IDE AI edits
python3 project_sync.py --errors

# Dump one specific file in full when Claude needs it
python3 project_sync.py --file vector_ships.py
```

---

## How To Use This Pattern

**Session start:**
1. Run `python3 project_sync.py` and paste output to creative AI
2. Creative AI is now fully context-aware
3. Discuss architecture, design problems, complex tasks

**Getting work done:**
1. Creative AI writes or updates tasks in `ai_instructions.json`
2. You tell Cursor: *"Read ai_instructions.json and implement TASK_002 exactly as specified"*
3. Cursor implements. You test.
4. Update task status to `done`

**Between sessions:**
1. Run `python3 project_sync.py --diff` to see what changed
2. At next session start, paste full sync output — creative AI is back up to speed instantly

---

## Prompt Template for IDE AI

When giving Cursor a task, use this pattern:

```
Read ai_instructions.json.
Follow all conventions in _conventions exactly.
Implement [TASK_ID]: [task title].
Follow the exact_change specification.
Do not modify any files listed in _architecture.do_not_touch.
Do not deviate from design_decisions without flagging it first.
```

---

## Why The Quality Gap Exists

IDE AI tools are optimised for a narrow, predictable task — complete this line, fix this bug, don't surprise me. That's a deliberate product decision. The blandness is a feature for fast mechanical work.

Creative AI is optimised for engagement with the whole problem — understanding context, forming a view, pushing back when something is wrong, making the connection between what you asked for and what you actually need.

You cannot use a scalpel to design a hospital. You cannot use an architect to perform surgery. This pattern uses each tool for what it is actually good at, with a coordination layer so they compound each other rather than operating in isolation.

---

## Origin

This pattern emerged during the development of a Python/Arcade space game — a project complex enough to require both deep architectural thinking (AI behaviour systems, spatial audio design, vector graphics pipelines) and substantial mechanical implementation (data structures, file I/O, Arcade 3.x API compatibility).

The insight: different AI tools have fundamentally different strengths, and the gap between them is not a bug to work around but a division of labour to formalise.

---

## Licence

**Creative Commons Attribution 4.0 International (CC BY 4.0)**

Copyright 2026 Shane Drobnick

You are free to:
- **Use** — personally, commercially, in products and services
- **Adapt** — build on it, modify it, extend it
- **Share** — distribute it, teach it, publish it

Under the following terms:
- **Attribution required** — You must credit Shane Drobnick as the originator of The Multi-AI Bridge Pattern and include a link to this repository
- **No additional restrictions** — You may not apply terms that prevent others from doing what this licence allows

Full licence: https://creativecommons.org/licenses/by/4.0/

---

## Author

**Shane Drobnick**
Software Engineer — Australia

*"The engineers who figure out how to orchestrate multiple AIs efficiently are going to be very valuable very soon."*
