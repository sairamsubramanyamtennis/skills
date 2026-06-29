# Agentic Design Pattern Catalog (comprehensive)

The full map of design patterns in the agentic-application space, organized into
eight families. Each entry gives **Intent** (what it is), **When** (where it
fits), **Watch** (the main trade-off or failure mode), and **Seen in** (where the
pattern shows up in the ecosystem — framework name, paper, or product).

This catalog aims to be *exhaustive of the space*, not a menu for one task. Many
patterns compose: a real system might be an agentic-RAG ReAct agent under a
supervisor, with reflection, persistence, and human approval. The families are a
way to navigate, not hard walls.

## Table of contents

1. **Reasoning & cognition** — how a single agent thinks
   1.1 Chain-of-Thought · 1.2 Self-Consistency · 1.3 ReAct · 1.4 Reflection /
   Self-Critique · 1.5 Reflexion · 1.6 Tree of Thoughts · 1.7 Graph of Thoughts ·
   1.8 Language Agent Tree Search (LATS)
2. **Planning & decomposition** — how work gets broken down
   2.1 Plan-and-Execute · 2.2 ReWOO · 2.3 LLM Compiler · 2.4 Recursive task
   decomposition · 2.5 Goal-driven / HTN
3. **Workflow orchestration** — predefined control flow
   3.1 Prompt Chaining · 3.2 Routing · 3.3 Parallelization (Sectioning) ·
   3.4 Parallelization (Voting) · 3.5 Map-Reduce · 3.6 Orchestrator-Workers ·
   3.7 Evaluator-Optimizer
4. **Multi-agent collaboration** — many agents together
   4.1 Supervisor · 4.2 Network / Swarm / Handoff · 4.3 Hierarchical / Teams ·
   4.4 Multi-Agent Debate · 4.5 Blackboard · 4.6 Role-Play / Society of Mind ·
   4.7 Mixture-of-Agents
5. **Tool use & action** — how an agent affects the world
   5.1 Tool / Function Calling · 5.2 Code-as-Action (CodeAct) · 5.3 Computer Use /
   GUI agents · 5.4 Model Context Protocol (MCP) · 5.5 Toolformer-style tool learning
6. **Retrieval & knowledge (RAG family)** — grounding in external data
   6.1 Naive RAG · 6.2 Agentic RAG · 6.3 Corrective RAG (CRAG) · 6.4 Self-RAG ·
   6.5 Adaptive RAG · 6.6 GraphRAG · 6.7 Query routing / multi-index
7. **Memory** — state within and across runs
   7.1 Short-term / working · 7.2 Semantic · 7.3 Episodic · 7.4 Procedural ·
   7.5 Memory management
8. **Control, safety & operations** — cross-cutting concerns
   8.1 Human-in-the-Loop · 8.2 Human-on-the-Loop · 8.3 Persistence / Checkpointing ·
   8.4 Guardrails & Validation · 8.5 Observability / Tracing / Evals ·
   8.6 Context management · 8.7 Sandboxing & permissions

---

## 1. Reasoning & cognition

How a single LLM agent reasons toward an answer. These are the "thinking"
strategies that everything else builds on.

### 1.1 Chain-of-Thought (CoT)
- **Intent.** Prompt the model to produce intermediate reasoning steps before the
  answer, improving accuracy on multi-step problems.
- **When.** Any task with reasoning depth (math, logic, planning). The substrate
  beneath ReAct and most agent loops.
- **Watch.** More tokens; reasoning can be confidently wrong. Zero-shot ("think
  step by step") vs. few-shot exemplars.
- **Seen in.** Wei et al. 2022; built into virtually every agent prompt and into
  "reasoning" models that do it internally.

### 1.2 Self-Consistency
- **Intent.** Sample several independent CoT traces and take the majority answer,
  trading compute for reliability.
- **When.** High-stakes single answers where one chain might slip; verifiable
  short answers.
- **Watch.** N× cost; needs an aggregation rule for ties/disagreement. The
  single-agent cousin of the [Voting](#34-parallelization-voting) workflow.
- **Seen in.** Wang et al. 2022; common in eval harnesses.

### 1.3 ReAct (Reason + Act)
- **Intent.** Interleave reasoning and tool actions in a loop: think → act
  (tool) → observe → repeat, until the model emits a final answer.
- **When.** The default agent pattern for open-ended, tool-using tasks where the
  number/order of steps is unknown. The workhorse of the whole space.
- **Watch.** Must bound iterations; loops on illegible tool errors; context grows
  every turn. See [Tool/Function Calling](#51-tool--function-calling) and
  [Context management](#86-context-management).
- **Seen in.** Yao et al. 2022; LangGraph `create_react_agent`, LangChain agents,
  Claude Agent SDK loop, nearly every framework's default agent.

### 1.4 Reflection / Self-Critique
- **Intent.** After producing output, the agent critiques it against goals/criteria
  and revises before finalizing.
- **When.** Quality-critical outputs the model can meaningfully improve on a
  fresh-eyes pass; verifying tool results before trusting them.
- **Watch.** Self-evaluation has blind spots — an external check (tests, a separate
  evaluator) is stronger. Cap the rounds. The agent-internal form of
  [Evaluator-Optimizer](#37-evaluator-optimizer).
- **Seen in.** "Reflection" agents in LangGraph/LlamaIndex; Madaan et al.
  "Self-Refine" 2023.

### 1.5 Reflexion
- **Intent.** Reflection with *memory*: the agent records verbal self-feedback
  about failed attempts and carries it into the next attempt, learning across
  tries within a task.
- **When.** Tasks you retry until success (coding, games, search) where lessons
  from failure should persist.
- **Watch.** Needs an episodic memory of attempts; reflections can entrench a
  wrong theory. Combines [Reflection](#14-reflection--self-critique) +
  [Episodic memory](#73-episodic).
- **Seen in.** Shinn et al. 2023 (Reflexion).

### 1.6 Tree of Thoughts (ToT)
- **Intent.** Explore multiple reasoning branches as a tree, evaluating and
  expanding promising states, backtracking from dead ends — deliberate search
  over thoughts rather than one linear chain.
- **When.** Problems needing exploration/look-ahead where a greedy chain fails
  (puzzles, planning, creative search).
- **Watch.** Expensive (many model calls); needs a state evaluator and a search
  policy (BFS/DFS/beam).
- **Seen in.** Yao et al. 2023; LangGraph ToT examples.

### 1.7 Graph of Thoughts (GoT)
- **Intent.** Generalize ToT to an arbitrary graph: thoughts can be merged,
  aggregated, and refined, not just branched — enabling combine/aggregate moves a
  tree can't express.
- **When.** Decomposable problems where partial solutions should be merged
  (sorting, aggregation-heavy reasoning).
- **Watch.** Even more orchestration overhead than ToT; clearest gains on
  structured tasks.
- **Seen in.** Besta et al. 2023 (Graph of Thoughts).

### 1.8 Language Agent Tree Search (LATS)
- **Intent.** Unify reasoning, acting, and planning: Monte-Carlo-style tree search
  over actions, with ReAct steps, reflection, and value backpropagation.
- **When.** Hard agentic tasks where you can afford heavy search for a better
  trajectory (complex tool use, web tasks).
- **Watch.** Among the most expensive patterns; needs a reward/value signal.
  Composes ToT + ReAct + Reflection.
- **Seen in.** Zhou et al. 2023 (LATS); LangGraph LATS tutorial.

---

## 2. Planning & decomposition

How an agent turns a goal into an ordered set of subtasks. ReAct decides the next
step each turn; these patterns commit to more structure up front.

### 2.1 Plan-and-Execute
- **Intent.** Generate a full multi-step plan first, then execute steps in turn,
  optionally re-planning when reality diverges.
- **When.** Long tasks where step-by-step ReAct drifts or wastes tokens; when an
  inspectable/approvable plan is valuable.
- **Watch.** Rigid plans break on surprises — allow re-planning; planner can emit
  vague steps. More moving parts than ReAct.
- **Seen in.** LangGraph "plan-and-execute"; BabyAGI lineage.

### 2.2 ReWOO (Reasoning WithOut Observation)
- **Intent.** Plan *all* tool calls up front (with variable placeholders for
  results), execute them, then do one final reasoning pass — decoupling planning
  from observations to cut LLM calls and token use.
- **When.** Tool-heavy tasks where steps don't depend on each other's content and
  you want fewer, cheaper model calls than ReAct.
- **Watch.** Breaks when a later step genuinely needs an earlier result to decide
  what to do (true dependency). Less adaptive than ReAct.
- **Seen in.** Xu et al. 2023 (ReWOO); LangGraph ReWOO tutorial.

### 2.3 LLM Compiler
- **Intent.** Have the LLM emit a DAG of tool calls, then a scheduler executes
  independent calls in parallel and resolves dependencies — speeds up and cheapens
  multi-tool tasks vs. sequential ReAct.
- **When.** Many tool calls with exploitable parallelism (fan-out lookups,
  multi-API gathering).
- **Watch.** Planner must express dependencies correctly; complexity in the
  scheduler. Related to [Map-Reduce](#35-map-reduce).
- **Seen in.** Kim et al. 2023 (LLMCompiler); LangGraph implementation.

### 2.4 Recursive task decomposition
- **Intent.** Split a task into subtasks, and recursively split subtasks that are
  still too big, until each is directly solvable — then compose results upward.
- **When.** Large, hierarchical problems (write a book, refactor a large codebase)
  that don't fit one context.
- **Watch.** Decomposition can over/under-shoot; needs a recombination strategy
  and a depth/branch cap. Basis of [Orchestrator-Workers](#36-orchestrator-workers)
  and [Hierarchical](#43-hierarchical--teams) agents.
- **Seen in.** HuggingGPT, AutoGPT-style task lists, "recursive summarization".

### 2.5 Goal-driven / Hierarchical Task Networks
- **Intent.** Represent goals and the sub-goals/methods that achieve them
  explicitly; the agent selects methods to satisfy goals, classical-planning style.
- **When.** Domains with well-defined operators and preconditions where you want
  reliability over open-ended reasoning.
- **Watch.** Requires modeling the domain; less flexible than free-form LLM
  planning. Often hybridized (LLM proposes, planner validates).
- **Seen in.** Classical AI planning; LLM-modulo and "LLM+P" approaches.

---

## 3. Workflow orchestration

Predefined control flow you write, with LLM calls inside. Predictable,
testable, cheaper than agents — prefer these when the path is known in advance.

### 3.1 Prompt Chaining
- **Intent.** Fixed sequence of steps, each LLM call refining the previous output,
  with optional programmatic gates between steps.
- **When.** Subtasks and order are known (outline → draft → polish; extract →
  translate → format).
- **Watch.** Errors compound — validate between steps. Don't chain what one good
  call could do.
- **Seen in.** LangChain LCEL pipes; the canonical workflow.

### 3.2 Routing
- **Intent.** Classify the input, then dispatch to a specialized handler (prompt,
  tools, or model).
- **When.** Distinct input categories needing different handling; cheap-model vs.
  strong-model triage.
- **Watch.** Misroutes are silent — measure router accuracy; keep a fallback.
- **Seen in.** LangChain `RunnableBranch`; "semantic router" libraries.

### 3.3 Parallelization — Sectioning
- **Intent.** Split a task into independent subtasks, run concurrently, aggregate.
- **When.** Genuinely independent subtasks (analyze N docs); a guardrail model
  running alongside the main one.
- **Watch.** Aggregation logic hides bugs; don't parallelize dependent steps.
- **Seen in.** LangChain `RunnableParallel`; LangGraph `Send` API.

### 3.4 Parallelization — Voting
- **Intent.** Run the *same* task multiple times (varied prompt/temperature) and
  aggregate by majority/threshold for confidence.
- **When.** You want diversity/robustness and can afford N× calls.
- **Watch.** N× cost; decide ties explicitly. Workflow form of
  [Self-Consistency](#12-self-consistency).
- **Seen in.** Ensemble prompting; guardrail "n-of-m" checks.

### 3.5 Map-Reduce
- **Intent.** Map an operation over many items in parallel, then reduce the
  results into one output.
- **When.** Summarize/extract over large collections that don't fit one context.
- **Watch.** Reduce step can lose detail; multi-level reduce for very large N.
- **Seen in.** LangChain map-reduce chains; LangGraph `Send` fan-out.

### 3.6 Orchestrator-Workers
- **Intent.** A central LLM dynamically decomposes a task, dispatches subtasks to
  workers, and synthesizes results — decomposition decided at runtime.
- **When.** You can't predict the breakdown up front (edit N relevant files,
  research across chosen sources). The workflow→agent boundary.
- **Watch.** Can over/under-decompose; cap worker count; synthesis needs
  structured worker output.
- **Seen in.** Anthropic "orchestrator-workers"; LangGraph subgraph fan-out.

### 3.7 Evaluator-Optimizer (Generator-Critic)
- **Intent.** One model generates, another evaluates against criteria and gives
  feedback, the generator revises — loop until it passes or a cap is hit.
- **When.** Clear evaluation criteria and iteration measurably helps (translation,
  code, structured writing).
- **Watch.** Always cap rounds; evaluator needs concrete criteria. Two-role form
  of [Reflection](#14-reflection--self-critique).
- **Seen in.** Anthropic "evaluator-optimizer"; reflection graphs.

---

## 4. Multi-agent collaboration

Multiple agents, each with its own role/tools/context, working together. Power at
the cost of coordination overhead and less predictability — justify the structure.

### 4.1 Supervisor
- **Intent.** A supervisor agent routes work to specialist agents and takes
  control back between handoffs (star topology); specialists don't talk directly.
- **When.** Task splits into specialties (researcher/coder/writer); you want
  central control and easy extension. The default multi-agent shape — start here.
- **Watch.** Supervisor is a bottleneck/SPOF; define each remit crisply; each
  handoff is a round-trip.
- **Seen in.** LangGraph `langgraph-supervisor`; CrewAI hierarchical; OpenAI
  Agents SDK handoffs.

### 4.2 Network / Swarm / Handoff
- **Intent.** Agents hand off directly to one another, peer-to-peer, with no
  central coordinator; any agent picks who acts next.
- **When.** Decentralized problems or conversational handoff (triage → billing →
  refunds).
- **Watch.** Hardest topology to debug; handoff loops — add cycle detection and a
  global step cap. Often a supervisor is simpler.
- **Seen in.** OpenAI Swarm / Agents SDK handoffs; LangGraph "network" multi-agent.

### 4.3 Hierarchical / Teams
- **Intent.** Supervisors of supervisors: teams of agents under team leads under a
  top supervisor — generalizes the supervisor pattern to scale.
- **When.** Too many specialists for one supervisor's context; functional
  divisions (research team, eng team).
- **Watch.** Latency/token overhead from coordination layers; only at real scale.
- **Seen in.** LangGraph hierarchical agent teams; CrewAI nested crews.

### 4.4 Multi-Agent Debate
- **Intent.** Several agents argue/critique a question across rounds; agreement or
  a judge yields a more reliable answer than a single pass.
- **When.** Hard reasoning/factuality tasks where adversarial cross-checking
  reduces error.
- **Watch.** Costly (agents × rounds); can converge on a shared wrong view;
  needs a termination/judge rule.
- **Seen in.** Du et al. 2023 (debate); AutoGen group chat.

### 4.5 Blackboard
- **Intent.** Agents share a common "blackboard" (shared memory); each reads the
  current state, contributes what it can, until the problem is solved — control is
  data-driven, not a fixed pipeline.
- **When.** Many specialists contribute opportunistically to a shared evolving
  solution (classic for sensor fusion / complex assembly).
- **Watch.** Coordination and write-conflict management; emergent control is hard
  to trace. A classic AI pattern resurfacing in LLM systems.
- **Seen in.** Classical blackboard architecture; shared-scratchpad multi-agent
  designs.

### 4.6 Role-Play / Society of Mind
- **Intent.** Agents adopt complementary roles (e.g. user + assistant, or several
  personas) and converse to solve a task or generate data.
- **When.** Task decomposition by persona; synthetic dialogue/data generation;
  brainstorming with diverse viewpoints.
- **Watch.** Role drift; can loop on pleasantries — keep prompts task-anchored.
- **Seen in.** CAMEL (role-playing agents); Minsky's "Society of Mind" framing;
  AutoGen personas.

### 4.7 Mixture-of-Agents
- **Intent.** Multiple agents/models each produce a candidate; later layers
  aggregate and refine across the candidates to beat any single model.
- **When.** You can afford several models and want quality above any one of them.
- **Watch.** Cost; aggregator quality is the ceiling. Multi-agent cousin of
  [Voting](#34-parallelization-voting)/[Mixture-of-Experts].
- **Seen in.** Wang et al. 2024 (Mixture-of-Agents).

---

## 5. Tool use & action

How an agent affects the world beyond text. Tool quality usually determines agent
success more than model or prompt.

### 5.1 Tool / Function Calling
- **Intent.** The model emits a structured call (name + JSON args); your code runs
  it and returns the result into the loop. The action substrate of ReAct.
- **When.** Any agent that must do more than talk (search, query, compute, write).
- **Watch.** Treat tool defs like an API for a smart stranger — sharp names, tight
  descriptions, recoverable errors, minimal surface. Too many tools confuse
  selection.
- **Seen in.** Native tool/function calling in every major model API; bind_tools
  across frameworks.

### 5.2 Code-as-Action (CodeAct)
- **Intent.** The agent's action space *is* code: it writes and executes code
  (often Python) instead of choosing from a fixed tool list — more expressive,
  composes operations in one step.
- **When.** Data analysis, automation, anything where composing logic beats
  picking discrete tools; "tools" become library functions the code calls.
- **Watch.** Requires a secure sandbox; arbitrary code is a real risk surface.
- **Seen in.** Wang et al. 2024 (CodeAct); HF `smolagents` CodeAgent; OpenAI code
  interpreter.

### 5.3 Computer Use / GUI agents
- **Intent.** The agent perceives a screen (screenshots/DOM) and acts via mouse,
  keyboard, and navigation — operating software built for humans.
- **When.** No API exists; automating GUI apps, browsers, desktops.
- **Watch.** Slow, brittle to UI changes, high-risk (can click anything) — sandbox
  and gate. Latency-heavy perception loop.
- **Seen in.** Anthropic Computer Use; OpenAI Operator; browser-agent frameworks
  (browser-use, WebVoyager).

### 5.4 Model Context Protocol (MCP)
- **Intent.** An open standard for connecting agents to tools/data/prompts via
  servers — a universal adapter so any MCP-speaking agent can use any MCP tool.
- **When.** You want reusable, portable tool integrations instead of bespoke glue
  per framework.
- **Watch.** Server trust/permissions; tool sprawl. It's an integration standard,
  not a reasoning pattern — but it shapes how modern agents get capabilities.
- **Seen in.** Anthropic MCP; supported by Claude Agent SDK, LangGraph, OpenAI
  Agents SDK, and most current frameworks.

### 5.5 Toolformer-style tool learning
- **Intent.** The model learns *when and how* to call tools from self-supervised
  data, rather than being prompted per task.
- **When.** Research/training-time concern; relevant when building tool-use into a
  model itself.
- **Watch.** Training cost; mostly upstream of application design.
- **Seen in.** Schick et al. 2023 (Toolformer).

---

## 6. Retrieval & knowledge (RAG family)

Grounding agents in external/private data. Ranges from a fixed retrieve-then-read
pipeline to fully agentic retrieval the model drives.

### 6.1 Naive RAG
- **Intent.** Retrieve top-k chunks for the query, stuff into context, generate an
  answer. Not agentic by itself — the baseline.
- **When.** Simple Q&A over a corpus where one retrieval suffices.
- **Watch.** Garbage retrieval → garbage answer; no recovery if the first pull is
  wrong. Chunking/embedding quality dominates.
- **Seen in.** Every RAG framework (LangChain, LlamaIndex, Haystack).

### 6.2 Agentic RAG
- **Intent.** Expose retrieval as a tool the agent decides when/whether/how to
  call, can issue multiple/iterative queries, and combine sources.
- **When.** Multi-hop questions; when the agent should choose among indexes or
  decide retrieval isn't needed.
- **Watch.** More calls/latency; the agent can over- or under-retrieve. Turns RAG
  from a pipeline into a [ReAct](#13-react-reason--act) loop.
- **Seen in.** LlamaIndex agentic RAG; LangGraph agentic-RAG tutorial.

### 6.3 Corrective RAG (CRAG)
- **Intent.** Grade retrieved docs for relevance; if weak, correct course — e.g.
  fall back to web search or re-query — before generating.
- **When.** Corpora with patchy coverage where bad retrieval is common and you
  want a safety net.
- **Watch.** Needs a relevance grader; adds a step. Composes retrieval +
  [Routing](#32-routing).
- **Seen in.** Yan et al. 2024 (CRAG); LangGraph CRAG tutorial.

### 6.4 Self-RAG
- **Intent.** The model decides *whether* to retrieve, then critiques retrieved
  passages and its own output with reflection tokens (relevant? supported?).
- **When.** You want retrieval on-demand plus self-checking for grounding/citation
  faithfulness.
- **Watch.** More complex generation; reflection adds calls. Combines RAG +
  [Reflection](#14-reflection--self-critique).
- **Seen in.** Asai et al. 2023 (Self-RAG); LangGraph Self-RAG tutorial.

### 6.5 Adaptive RAG
- **Intent.** Route each query by difficulty to the right strategy — no retrieval
  for simple, single-shot for moderate, iterative/multi-hop for complex.
- **When.** Mixed query workloads where one-size retrieval wastes effort or
  underperforms.
- **Watch.** Needs a reliable difficulty classifier. Retrieval-flavored
  [Routing](#32-routing).
- **Seen in.** Jeong et al. 2024 (Adaptive-RAG); LangGraph tutorial.

### 6.6 GraphRAG
- **Intent.** Build a knowledge graph from the corpus and retrieve over graph
  structure/communities, enabling global, connect-the-dots questions a flat vector
  store can't answer.
- **When.** "What are the themes across this whole corpus?" / entity-relationship
  questions.
- **Watch.** Expensive graph construction; overkill for simple lookup.
- **Seen in.** Microsoft GraphRAG; LlamaIndex/Neo4j knowledge-graph RAG.

### 6.7 Query routing / multi-index
- **Intent.** Route a query to the right index/datasource (or several) and merge —
  picking the best knowledge source per question.
- **When.** Multiple corpora/tools (docs vs. tickets vs. SQL); structured +
  unstructured mix.
- **Watch.** Routing accuracy; result fusion across heterogeneous sources.
- **Seen in.** LlamaIndex routers/sub-question engine; LangChain multi-retriever.

---

## 7. Memory

What the agent remembers within a run and across runs. Memory management is often
the difference between a demo and a usable agent.

### 7.1 Short-term / working memory
- **Intent.** The run's scratchpad: message history, intermediate results, the
  working set, held in the agent's state.
- **When.** Every multi-step agent.
- **Watch.** Grows every turn — overflow degrades attention; manage actively
  (see [Context management](#86-context-management)).
- **Seen in.** LangGraph state / `MessagesState`; SDK session context.

### 7.2 Semantic memory
- **Intent.** Long-term store of *facts* (user preferences, domain knowledge),
  retrieved by key or similarity across sessions.
- **When.** Personalization; agents that should "know" stable facts about a
  user/domain.
- **Watch.** Write policy (what's worth storing); retrieval noise; namespacing per
  user.
- **Seen in.** LangGraph `Store`; mem0; vector-store memory.

### 7.3 Episodic memory
- **Intent.** Long-term store of *experiences* — past interactions/trajectories,
  often used as few-shot examples or for learning from past episodes.
- **When.** Agents that should recall "last time I did X, Y happened"; few-shot
  from history; powers [Reflexion](#15-reflexion).
- **Watch.** Retrieval relevance; stale episodes; storage growth.
- **Seen in.** Generative Agents (Park et al. 2023); agent memory libraries.

### 7.4 Procedural memory
- **Intent.** Long-term memory of *how to do things* — skills/procedures, often
  baked into the system prompt or a learned skill library the agent reuses.
- **When.** Agents that accumulate reusable skills (e.g. Voyager's skill library).
- **Watch.** Keeping the skill set coherent and discoverable; versioning.
- **Seen in.** Voyager (Wang et al. 2023) skill library; prompt/tool libraries.

### 7.5 Memory management
- **Intent.** The policies that keep memory useful: summarization/compaction of
  long histories, what to write vs. forget, retrieval strategy, trimming.
- **When.** Any long-running or long-context agent.
- **Watch.** Over-summarizing loses detail; naive "store everything" retrieves
  noise. This is an active design choice, not a default.
- **Seen in.** LangGraph summarization nodes; SDK auto-compaction; MemGPT-style
  paging.

---

## 8. Control, safety & operations

Cross-cutting concerns that wrap any pattern above. Production agents combine
several. None are optional at scale.

### 8.1 Human-in-the-Loop (HITL)
- **Intent.** Insert human judgment into the flow — approve/reject, edit the
  proposed action/state, or provide requested input — by pausing and resuming.
- **When.** Irreversible/side-effecting actions (pay, send, delete, trade, prod
  writes); low failure tolerance; compliance.
- **Watch.** Needs persistence to pause/resume cleanly; gate the *consequential*
  steps, not everything (don't make the human the bottleneck).
- **Seen in.** LangGraph `interrupt()`; Claude Agent SDK `can_use_tool` /
  permission modes; approval gates everywhere.

### 8.2 Human-on-the-Loop
- **Intent.** Human *monitors* an autonomous agent and can intervene/override,
  rather than approving each step — oversight without per-action gating.
- **When.** Higher-autonomy systems where step-by-step approval is impractical but
  you still need a kill switch and audit.
- **Watch.** Requires real-time observability and a fast override path; alerting on
  anomalies.
- **Seen in.** Ops dashboards over agent fleets; "supervised autonomy" designs.

### 8.3 Persistence / Checkpointing
- **Intent.** Save agent state per step to durable storage — enabling resume after
  crash, pause/continue, HITL, time-travel/branching, and audit.
- **When.** Long-running, interruptible, human-gated, or failure-sensitive agents.
- **Watch.** State must be serializable; choose granularity; namespace by
  thread/session.
- **Seen in.** LangGraph checkpointers (Memory/SQLite/Postgres); durable-execution
  engines (Temporal-style).

### 8.4 Guardrails & Validation
- **Intent.** Constraints around the agent enforced in *code*, independent of the
  model: input guards (injection/off-topic), output guards (schema/policy/
  fact-check), action guards (allow/deny lists, rate/spend limits, sandboxing).
- **When.** Anytime the model touches untrusted input or consequential actions.
- **Watch.** A guardrail the model can argue past isn't one — enforce outside the
  model. Balance safety vs. false-positive friction.
- **Seen in.** NeMo Guardrails, Guardrails AI, Llama Guard; OpenAI Agents SDK
  guardrails; SDK hooks/permissions.

### 8.5 Observability / Tracing / Evals
- **Intent.** Trace every run — each LLM call, tool call, state transition,
  decision — and evaluate behavior over time. You can't operate what you can't see.
- **When.** From the first version of any agent; non-negotiable for production.
- **Watch.** Agents fail nondeterministically in ways unit tests miss; keep
  run/thread IDs to reconstruct sessions; pair traces with offline evals.
- **Seen in.** LangSmith, LangFuse, Arize Phoenix, OpenTelemetry GenAI; SDK
  PreToolUse/PostToolUse hooks.

### 8.6 Context management
- **Intent.** Actively curate what's in the context window — trimming, summarizing,
  retrieving the right working set, ordering — so the model stays effective as
  history grows.
- **When.** Long ReAct loops, long conversations, large tool outputs.
- **Watch.** "Context rot" / lost-in-the-middle; cost; over-trimming drops needed
  facts. Closely tied to [Memory management](#75-memory-management).
- **Seen in.** SDK auto-compaction; LangGraph trim/summarize nodes; MemGPT paging.

### 8.7 Sandboxing & permissions
- **Intent.** Run side-effecting actions (code exec, file/network/system access)
  in an isolated, least-privilege environment with explicit permission scopes.
- **When.** Any agent that runs code, touches a filesystem/network, or acts on
  real systems — especially [CodeAct](#52-code-as-action-codeact) and
  [Computer Use](#53-computer-use--gui-agents).
- **Watch.** Sandbox escape; over-broad permissions; "bypass permissions" modes on
  real data. Defense in depth with [Guardrails](#84-guardrails--validation).
- **Seen in.** Code-interpreter sandboxes (E2B, Docker); SDK permission modes;
  OS-level isolation.

---

## How to read this map for a given problem

- **Pick a primary reasoning/agent pattern** (Family 1–2): usually ReAct; escalate
  to plan-based or search-based (ToT/LATS) only when a linear loop visibly fails.
- **Or stay a workflow** (Family 3) if the path is known — it's cheaper and safer.
- **Add collaboration** (Family 4) only when one agent's context/skills are
  genuinely overloaded; default to supervisor.
- **Choose action + knowledge** (Families 5–6): function-calling vs. CodeAct vs.
  computer-use; naive vs. agentic/corrective/adaptive RAG.
- **Decide memory** (Family 7): working memory always; add long-term types only as
  needed.
- **Always layer the cross-cutting ones** (Family 8) to taste: observability and
  bounded loops always; persistence, HITL, guardrails, and sandboxing as stakes
  rise.

For *which framework expresses which of these*, see `frameworks.md`.
