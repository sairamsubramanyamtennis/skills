# Frameworks → patterns map

Which open-source frameworks support which design patterns, what they *call*
them, and what's distinctive about each. Use this to understand the agentic
ecosystem and to translate a pattern name into a given framework's vocabulary.
Patterns referenced here are defined in `patterns.md`.

Quick orientation: most frameworks fall on a spectrum from **graph/explicit**
(you wire control flow) to **role/declarative** (you describe agents and let the
framework orchestrate).

| Framework | Abstraction | Sweet spot |
|---|---|---|
| LangGraph | Graph of state + nodes + edges | Complex, controllable agent/workflow control flow |
| LangChain | Composable components (LCEL) + `create_agent` | Chains, RAG, quick tool-calling agents |
| LlamaIndex | Data/query engines + agents | RAG-centric and agentic retrieval |
| CrewAI | Roles + tasks + crews | Role-based teams, fast to stand up |
| AutoGen / AG2 | Conversable agents + group chat | Conversational multi-agent, debate, code-exec |
| OpenAI Agents SDK (+ Swarm) | Agents + handoffs + guardrails | Lightweight handoff-style multi-agent |
| Claude Agent SDK | Built-in loop + tools/MCP + subagents | Building directly on Claude with minimal glue |
| Semantic Kernel | Plugins + planners | Enterprise/.NET, planner-driven orchestration |
| Haystack | Pipelines of components | Production RAG/search pipelines |
| DSPy | Programs + optimizers | Optimizing/compiling prompts & pipelines |
| Pydantic AI | Typed agents | Type-safe, production Python agents |
| Google ADK | Agents + workflow agents | Gemini-centric multi-agent + deployment |
| Microsoft Agent Framework | Workflows + agents | Convergence of SK + AutoGen |

---

## LangGraph
- **Abstraction.** Explicit graph: typed **state**, **nodes** (functions),
  **edges** (fixed or conditional), reducers, `START`/`END`. Compile with a
  checkpointer.
- **Patterns it expresses well.** Nearly all control-flow patterns — ReAct
  (`create_react_agent`), Plan-and-Execute, ReWOO, LLM Compiler, ToT, LATS,
  Reflection, Evaluator-Optimizer, Routing, Map-Reduce (`Send`),
  Orchestrator-Workers (subgraphs), Supervisor (`langgraph-supervisor`),
  Network/Hierarchical multi-agent, all RAG variants (agentic/CRAG/Self/Adaptive
  tutorials).
- **Cross-cutting.** Best-in-class HITL (`interrupt()`), persistence
  (Memory/SQLite/Postgres checkpointers), long-term memory (`Store`), streaming,
  time-travel. Observability via LangSmith.
- **Distinctive.** You see and control the loop — the reference implementation for
  most patterns in this catalog. Lower-level than role-based frameworks.

## LangChain
- **Abstraction.** Composable runnables wired with **LCEL** (`|`); modern
  `create_agent` (built on LangGraph). Models, prompts, parsers, retrievers, tools.
- **Patterns.** Prompt Chaining, Routing (`RunnableBranch`), Parallelization
  (`RunnableParallel`), Map-Reduce, naive + agentic RAG, Tool/Function Calling,
  ReAct via `create_agent`.
- **Cross-cutting.** Structured output, retrievers/loaders ecosystem; persistence
  & HITL inherited from LangGraph; LangSmith tracing.
- **Distinctive.** The broad "batteries-included" component library; the quickest
  path for chains/RAG. For real agent control flow it now points you to LangGraph.

## LlamaIndex
- **Abstraction.** Data-centric: indexes, query engines, retrievers, plus agents
  (`FunctionAgent`, `ReActAgent`) and multi-agent (`AgentWorkflow`).
- **Patterns.** The RAG family is its core — naive, **agentic RAG**, query
  routing/multi-index, sub-question decomposition, GraphRAG; also ReAct,
  Tool-calling, Supervisor-style `AgentWorkflow`.
- **Cross-cutting.** Rich ingestion/retrieval; workflow events; observability
  integrations.
- **Distinctive.** The go-to when retrieval over your data is the heart of the
  system; deepest RAG tooling.

## CrewAI
- **Abstraction.** **Roles** (agents with a goal/backstory/tools), **tasks**, and
  **crews**; processes are *sequential* or *hierarchical*. Also "Flows" for
  event-driven control.
- **Patterns.** Role-Play/teams, Supervisor (hierarchical process), sequential
  workflow, Tool-calling; delegation between agents.
- **Cross-cutting.** Simple memory, guardrails, callbacks.
- **Distinctive.** Declarative and fast to stand up a team; you describe roles, it
  orchestrates. Less low-level control than LangGraph.

## AutoGen / AG2
- **Abstraction.** **Conversable agents** that exchange messages;
  `GroupChat` + manager for many agents; `AssistantAgent` + `UserProxyAgent`
  (which can execute code).
- **Patterns.** Multi-Agent **Debate**/group chat, Role-Play, Supervisor (group
  chat manager), Code-as-Action (code-executing user proxy), Reflection, HITL via
  the human user-proxy.
- **Cross-cutting.** Built-in code execution, human input modes.
- **Distinctive.** Conversation-first multi-agent; strong for debate and
  code-writing agent teams. (AG2 is the community fork; Microsoft Agent Framework
  is the successor lineage.)

## OpenAI Agents SDK (and Swarm)
- **Abstraction.** **Agents** with instructions/tools, **handoffs** to other
  agents, **guardrails**, sessions, tracing. Swarm was the experimental
  predecessor; the Agents SDK is the production version.
- **Patterns.** Network/Swarm **Handoff** multi-agent, Routing, Supervisor-ish
  delegation, Tool-calling, ReAct loop.
- **Cross-cutting.** First-class **guardrails** (input/output), tracing, sessions;
  MCP support.
- **Distinctive.** Minimal, handoff-centric; very light abstraction for
  decentralized multi-agent.

## Claude Agent SDK
- **Abstraction.** Built-in ReAct loop (`query()` / `ClaudeSDKClient`), tools via
  `@tool`/in-process MCP, external MCP servers, **subagents**, hooks, permissions.
  Same harness as Claude Code.
- **Patterns.** ReAct (built in), Tool-calling, MCP integration,
  Supervisor/workers via subagents, HITL via `can_use_tool`/permission modes,
  Guardrails/Observability via hooks, automatic context management.
- **Distinctive.** Building directly on Claude with the least orchestration glue;
  context management and the loop are handled for you. Model-specific (Claude).

## Semantic Kernel
- **Abstraction.** **Plugins** (functions), **planners**, memory, and the newer
  Agent Framework abstractions; .NET-first, also Python/Java.
- **Patterns.** Planner-driven decomposition (Plan-and-Execute lineage),
  Tool/Function-calling, Routing, multi-agent (group chat), RAG.
- **Distinctive.** Enterprise integration and multi-language; planners as a
  first-class concept. Converging with AutoGen under Microsoft Agent Framework.

## Haystack
- **Abstraction.** **Pipelines** of components (retrievers, readers, generators,
  routers) as a graph; agents/tools on top.
- **Patterns.** RAG (naive → advanced), Routing, branching pipelines,
  Tool-calling, some agentic loops.
- **Distinctive.** Production-grade search/RAG pipelines with a mature component
  model; strong retrieval focus like LlamaIndex but pipeline-shaped.

## DSPy
- **Abstraction.** Declarative **programs** (modules with signatures) plus
  **optimizers** that compile/tune prompts and weights against a metric.
- **Patterns.** ReAct, CoT, RAG, multi-stage pipelines — but the headline is
  *optimizing* these rather than hand-prompting them.
- **Distinctive.** Treats prompting as a learnable program; orthogonal to the
  orchestration frameworks — you can optimize modules used inside them.

## Pydantic AI
- **Abstraction.** Typed agents with structured (Pydantic) outputs, tools,
  dependency injection, and a graph library for control flow.
- **Patterns.** Tool-calling, ReAct, Routing, structured workflows; HITL and
  durable execution integrations.
- **Distinctive.** Type-safety and a FastAPI-like developer feel for production
  Python agents.

## Google Agent Development Kit (ADK)
- **Abstraction.** `LlmAgent` plus **workflow agents** (Sequential, Parallel,
  Loop) and multi-agent composition; deployment to Vertex.
- **Patterns.** Sequential/Parallel/Loop workflows, Supervisor/Hierarchical
  multi-agent, Tool-calling, Routing.
- **Distinctive.** Gemini-centric, with explicit workflow-agent primitives and a
  managed deployment path.

## Microsoft Agent Framework
- **Abstraction.** Unifies Semantic Kernel + AutoGen: **workflows** (graph-based,
  typed) plus **agents** and group chat.
- **Patterns.** Workflow orchestration, multi-agent (handoff/group chat),
  Tool-calling, planners.
- **Distinctive.** Microsoft's consolidation play for enterprise agents; the
  forward path for SK/AutoGen users.

---

## Cross-reference: pattern → where to look

- **ReAct / Tool-calling** → all of them; cleanest in LangGraph, Claude Agent SDK,
  Pydantic AI.
- **Plan-and-Execute / ReWOO / LLM Compiler** → LangGraph tutorials; SK planners.
- **ToT / GoT / LATS** → LangGraph examples (research-grade; rare as built-ins).
- **Workflow (chain/route/parallel/map-reduce)** → LangChain LCEL, Haystack
  pipelines, Google ADK workflow agents.
- **Supervisor / Hierarchical** → LangGraph, CrewAI, AutoGen group chat, ADK.
- **Network / Handoff** → OpenAI Agents SDK, LangGraph network multi-agent.
- **Debate / Role-Play** → AutoGen, CAMEL, CrewAI.
- **RAG family (agentic/CRAG/Self/Adaptive/GraphRAG)** → LlamaIndex, LangGraph
  tutorials, Haystack; GraphRAG via Microsoft GraphRAG.
- **Memory (semantic/episodic/procedural)** → LangGraph `Store`, mem0, MemGPT,
  framework memory modules.
- **HITL / Persistence** → LangGraph (`interrupt()` + checkpointers), Claude Agent
  SDK permissions, durable-execution engines.
- **Guardrails** → OpenAI Agents SDK, NeMo Guardrails, Guardrails AI, Llama Guard.
- **Observability** → LangSmith, LangFuse, Arize Phoenix, OpenTelemetry GenAI.
- **CodeAct / Sandboxing** → smolagents, AutoGen code exec, E2B/Docker sandboxes.
- **Computer Use** → Anthropic Computer Use, OpenAI Operator, browser-use.
- **MCP** → Claude Agent SDK, LangGraph, OpenAI Agents SDK, and most current
  frameworks.
- **Optimization of any pattern** → DSPy.
