---
name: agentic-design-patterns
description: >-
  A comprehensive map of the design patterns used to build agentic AI systems —
  the whole landscape, drawn from LangGraph, LangChain, LlamaIndex, CrewAI,
  AutoGen, the OpenAI Agents SDK, the Claude Agent SDK, and the research
  literature. Use this skill whenever the user wants to understand, survey,
  compare, or learn agentic / LLM-agent design patterns: "what are the agent
  design patterns", "explain ReAct vs plan-and-execute", "multi-agent
  orchestration patterns", "what patterns does LangGraph support", "patterns for
  agent memory / RAG / tool use / reflection / human-in-the-loop", "how do agents
  coordinate", "give me the full picture of agentic architectures". Trigger even
  when a framework isn't named — the goal is understanding the pattern space, not
  running any one library. When invoked, present the complete catalog of patterns
  (organized by family), then go as deep as asked on any pattern or framework.
---

# Agentic Design Patterns — the full landscape

This skill is a **reference map of the entire agentic-design-pattern space**. Its
purpose is understanding: when invoked, lay out *all* the patterns used to build
agentic AI systems — what each is, when it's used, its trade-offs, and which
frameworks embody it — so the user can see the whole field and drill into any
part of it.

The user's goal is to **understand the patterns**, not to run a particular
framework. Frameworks (LangGraph, LangChain, LlamaIndex, CrewAI, AutoGen, OpenAI
Agents SDK, Claude Agent SDK, …) are cited as *where a pattern lives in the
ecosystem*, not as something to install. Don't push code or a specific stack
unless the user explicitly asks "show me how to build this."

## How to respond when this skill triggers

1. **Default: present the complete map.** Lay out the catalog below — all eight
   families and every pattern, each with its one-line essence. The point is
   coverage: the user should come away seeing the whole space. Keep each line
   tight; this is a map, not an essay.

2. **Then offer depth.** Invite the user to go deeper on any family, pattern, or
   framework. When they pick one, read the relevant reference file and give the
   fuller treatment (intent, when to use, trade-offs, where it's seen):
   - `references/patterns.md` — the comprehensive deep-dive catalog (every pattern
     with Intent / When / Watch / Seen-in, plus papers and framework homes).
   - `references/frameworks.md` — which framework supports which patterns, what
     each calls them, and what's distinctive about each.

3. **Match the ask.** If the user names a specific slice up front ("just the
   multi-agent ones", "compare ReAct and ReWOO", "what does CrewAI support"),
   skip the full dump and go straight there using the reference files — but
   mention the neighboring families so they know the rest of the map exists.

4. **Stay conceptual unless asked otherwise.** Explain patterns, trade-offs, and
   relationships. Only produce code/scaffolding if the user explicitly shifts to
   "help me build it."

## The complete pattern map

Eight families. Patterns compose freely across them — a real system is usually
several of these layered together. Full detail for every entry is in
`references/patterns.md`.

### 1 · Reasoning & cognition — how a single agent thinks
- **Chain-of-Thought (CoT)** — emit intermediate reasoning steps before answering.
- **Self-Consistency** — sample several reasoning traces, take the majority answer.
- **ReAct** — interleave reason → act (tool) → observe in a loop. *The workhorse.*
- **Reflection / Self-Critique** — critique own output and revise.
- **Reflexion** — reflection remembered across attempts; learn from past failures.
- **Tree of Thoughts (ToT)** — search a tree of reasoning branches, backtracking.
- **Graph of Thoughts (GoT)** — ToT generalized to merge/aggregate thoughts.
- **LATS** — tree search over actions fusing ReAct + reflection + value backup.

### 2 · Planning & decomposition — how work gets broken down
- **Plan-and-Execute** — plan all steps first, then execute (re-plan as needed).
- **ReWOO** — plan all tool calls up front, execute, then reason once (fewer calls).
- **LLM Compiler** — emit a DAG of tool calls; run independent ones in parallel.
- **Recursive task decomposition** — split, and split subtasks, until solvable.
- **Goal-driven / HTN** — explicit goals→sub-goals/methods, classical-planning style.

### 3 · Workflow orchestration — predefined control flow (cheaper, predictable)
- **Prompt Chaining** — fixed sequence, each call refines the last.
- **Routing** — classify input, dispatch to a specialized handler.
- **Parallelization — Sectioning** — split into independent subtasks, run at once.
- **Parallelization — Voting** — run the same task N times, aggregate for confidence.
- **Map-Reduce** — map over many items in parallel, then reduce.
- **Orchestrator-Workers** — coordinator decomposes *dynamically*, workers execute.
- **Evaluator-Optimizer** — generator + critic loop until it passes a bar.

### 4 · Multi-agent collaboration — many agents together
- **Supervisor** — a manager routes work to specialists (star topology). *Start here.*
- **Network / Swarm / Handoff** — agents hand off peer-to-peer, no central control.
- **Hierarchical / Teams** — supervisors of supervisors; scales the supervisor idea.
- **Multi-Agent Debate** — agents argue/critique across rounds for reliability.
- **Blackboard** — agents share a common memory and contribute opportunistically.
- **Role-Play / Society of Mind** — complementary personas converse to solve/generate.
- **Mixture-of-Agents** — many candidates, later layers aggregate and refine.

### 5 · Tool use & action — how an agent affects the world
- **Tool / Function Calling** — model emits structured calls; code runs them.
- **Code-as-Action (CodeAct)** — the action space *is* code the agent writes & runs.
- **Computer Use / GUI agents** — perceive a screen, act via mouse/keyboard.
- **Model Context Protocol (MCP)** — open standard for plugging in tools/data.
- **Toolformer-style tool learning** — model learns when/how to call tools (training).

### 6 · Retrieval & knowledge (RAG family) — grounding in external data
- **Naive RAG** — retrieve top-k, stuff context, generate (the baseline).
- **Agentic RAG** — retrieval as a tool the agent decides when/how to use.
- **Corrective RAG (CRAG)** — grade retrieved docs; correct course if weak.
- **Self-RAG** — model decides whether to retrieve, then critiques relevance/support.
- **Adaptive RAG** — route each query by difficulty to the right retrieval strategy.
- **GraphRAG** — retrieve over a knowledge graph for global, connect-the-dots Qs.
- **Query routing / multi-index** — send each query to the right source(s), merge.

### 7 · Memory — state within and across runs
- **Short-term / working** — the run's scratchpad (history, intermediate results).
- **Semantic** — long-term *facts* (preferences, knowledge) recalled across sessions.
- **Episodic** — long-term *experiences*/past trajectories; few-shot from history.
- **Procedural** — long-term *skills*/how-to, reused (e.g. a skill library).
- **Memory management** — summarize/compact, what to write vs. forget, retrieval policy.

### 8 · Control, safety & operations — cross-cutting (layer onto anything)
- **Human-in-the-Loop** — pause for a human to approve/edit/answer, then resume.
- **Human-on-the-Loop** — human monitors an autonomous agent and can override.
- **Persistence / Checkpointing** — durable state: resume, pause, time-travel, audit.
- **Guardrails & Validation** — code-enforced input/output/action constraints.
- **Observability / Tracing / Evals** — trace every step; evaluate over time.
- **Context management** — curate the window (trim/summarize/retrieve) as it grows.
- **Sandboxing & permissions** — isolate side-effecting actions, least privilege.

## How the families relate (the one-paragraph synthesis)

Families **1–2** are how an agent *thinks and plans*; **3** is when you hard-code
the flow instead (a workflow, not an agent — prefer it when the path is known);
**4** is what happens when *one agent isn't enough*; **5–6** are how an agent
*acts and grounds itself*; **7** is what it *remembers*; **8** is what keeps it
*safe, observable, and operable*. Most production systems pick a primary
reasoning/agent pattern, optionally wrap it in a workflow or multi-agent
structure, give it tools + retrieval + memory, and layer the cross-cutting
controls as the stakes rise. The art is using the *least* structure that solves
the problem.

## Reference files

- `references/patterns.md` — comprehensive catalog: every pattern with Intent /
  When / Watch (trade-off) / Seen-in (papers + framework homes). Read this for
  depth on any pattern.
- `references/frameworks.md` — the ecosystem: LangGraph, LangChain, LlamaIndex,
  CrewAI, AutoGen/AG2, OpenAI Agents SDK, Claude Agent SDK, Semantic Kernel,
  Haystack, DSPy, Pydantic AI, Google ADK, Microsoft Agent Framework — what each
  supports, its vocabulary, and a pattern→framework cross-reference.
