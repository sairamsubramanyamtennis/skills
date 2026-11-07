# Skill Registry

Maintained by `sagent`. **Never assume this file is current** — reconcile against live discovery
(§7 of SKILL.md) whenever routing matters.

Last reconciled: **2026-09-05** (against `~/.claude/skills/`, `~/.claude/agents/`, session skill
listing, and connected MCP servers).

---

## How to read this

Entries are grouped by domain. Anything marked **[built-in]** ships with Claude Code; everything
else is a user skill in `~/.claude/skills/`. `sagent` itself is not listed — it is the router.

---

# DOMAIN OWNERS — the staff (added 2026-10-08)

Three accountable agents with persistent memory sit above the specialists. They route to the
skills and bench agents below; nothing was replaced. Contract: `~/.claude/agent-memory/PROTOCOL.md`.
Dialogue: `/sagent standup` (interactive) and the `daily-standup` scheduled job (weekdays 07:30).

| Agent | Owns | Routes to | Memory |
|---|---|---|---|
| `equity-agent` | finance, investment, trading, every algo and research verdict, the bench, portfolio allocation | suffet · quantitative-momentum · qm-autoresearch · qm-recon · earnings-drift · us-etf-expert · pg-skill (read) · the 6 bench agents | `~/.claude/agent-memory/equity-agent/` |
| `tech-agent` | all technology: scheduled jobs, Postgres, APIs, scripts, harness, telemetry, recap, the machine; receives every `REQUEST tech-agent:` | sarch · claude-code-guide · pg-skill (the DB) · skill-creator · update-config · schedule · code-review | `~/.claude/agent-memory/tech-agent/` |
| `jyotish-agent` | Vedic + mundane astrology, every chart in `jyotish-readings\`, the lessons record (firewalled) | jyotish-reader · d1-image-to-text | `~/.claude/agent-memory/jyotish-agent/` |
| `datasci-agent` | astro-market laboratory (schema `astro_lab`), pre-registered tests of astro features vs ETF returns; sole astro↔market crossing point; added 2026-10-10 | the 6 bench agents · pg-skill (read `astro.*`) | `~/.claude/agent-memory/datasci-agent/` |
| `prianka-agent` | Prianka's creator career: her ~500K TikTok audience, the singing goal, the words→music bridge; reads only her TikTok Studio exports in `C:\Users\ssair\prianka\inbox\`, grades every suggestion; astrology-firewalled; added 2026-10-14 | smob-dic (advise only) · tech-agent (Display API app, weekly job) | `~/.claude/agent-memory/prianka-agent/` |

**When to call the owner vs the skill:** the owner when the outcome must be remembered, tracked or
defended later (a verdict, an allocation, a job that must keep running, a chart register change);
the skill directly for a one-off answer.

---

# DOMAIN: Investing, Trading & Quant Research

## Suffet
**Purpose:** Investment strategist, capital-allocation partner, quantitative research supervisor.
**Capabilities:** Stock/company/valuation analysis · thesis evaluation · portfolio and trade
decisions · options · macro and geopolitics · factor/signal/anomaly judgment · research prioritization
· prediction scorecard (`/suffet review`, `/suffet score`) · multi-agent research panels.
**Best used for:** Interpretation and judgment on any investment or research result.
**Inputs:** A ticker, thesis, result, or research question.
**Outputs:** Ranked judgment, challenge, portfolio implication, next research move.
**Related:** quantitative-momentum · qm-autoresearch · earnings-drift · pg-skill · us-etf-expert ·
the five research subagents.
**Note:** Suffet interprets; the mechanical skills compute. Route computation to them first.

## quantitative-momentum
**Purpose:** Wes Gray / Alpha Architect QM screener + backtester for S&P 500.
**Capabilities:** 6-1 momentum + FIP quality composite · point-in-time `--as-of` screens back to
~2004-05.
**Inputs:** Optional as-of date.  **Outputs:** Ranked screen / backtest.
**Related:** qm-autoresearch · qm-recon · pg-skill · suffet.

## qm-autoresearch
**Purpose:** Karpathy-style parameter optimizer for QM strategies.
**Note:** Memory says **stop re-parameterizing QM** — all three top configs flip sign at 2015.
Route new QM tuning requests through suffet before running this.

## qm-recon
**Purpose:** Reconcile QM Excel workbooks against Postgres `res.screen_result`. PASS/FAIL + exit code.

## earnings-drift
**Purpose:** Pre-earnings event-study desk on the Postgres EDGAR panel + 49M-row bar spine.
**Note:** Pre-earnings drift is **FALSIFIED** (t=1.74, placebo kills it). Stages 3-4 remain open.

## pg-skill
**Purpose:** Inventory and explain the local Postgres `trading` DB (localhost:5433).
**Critical rule it carries:** never join on a ticker string — use `ref.resolve`.
**Use before** writing any code that touches that database.

## us-etf-expert
**Purpose:** US ETF specialist — structures, mechanics, tax, liquidity, tracking error, product
categories, portfolio construction.

## smarket-intel
**Purpose:** Daily market intelligence briefing — market mode (indices, breadth, rotation, macro
calendar) or ticker mode. Supports `--as-of` for point-in-time briefings.
**Related:** the scheduled daily email job in `C:\Users\ssair\market-intel-daily\`.

### Research subagents (Agent tool) — the adversarial bench
| Agent | Seat |
|---|---|
| `hypothesis-author` | Pre-registers mechanism + prediction + kill rule **before** any number exists |
| `sort-runner` | Runs ONE variant, returns one compact row — fan out in parallel |
| `backtest-auditor` | Was the number computed correctly? |
| `null-advocate` | Does the number mean anything? Placebo, baseline, regime, multiple testing |
| `cost-capacity-realist` | What would the account actually have kept, at real size? |
| `boring-alternative` | Does it beat SPY / RSP / plain 6-1 / just holding? |

**Standing rule:** no performance figure enters the journal or memory until it has been through
this bench.

---

# DOMAIN: Career

## sscout
**Purpose:** Senior technology career scout — finds and scores openings 0-100 against Sai's profile.
**Inputs:** Company name, careers URL, or pasted JD.  **Outputs:** Ranked, red-flagged opportunities.
**Related:** sresume · sinterview-tutor · sarch.  **Has:** `memory/` (profile, companies, applications, lessons).

## sresume
**Purpose:** TechResume Architect — forensic resume review, positioning strategy, .docx/ATS/LinkedIn output.
**Related:** sscout · sinterview-tutor.

## sinterview-tutor
**Purpose:** Technical interview coach for senior/principal/architect/leadership rounds. Gap
analysis, prep plan, Socratic tutoring, story bank, mocks, system design, red team, readiness score.
**Orchestrates:** sscout (the job) + sarch (the depth).

---

# DOMAIN: AI / Architecture / Engineering

## sarch
**Purpose:** Principal LLM / GenAI / Agentic-Systems Architect persona.
**Covers:** foundation models · RAG and retrieval · agentic architecture · AI-assisted SWE ·
AI infra and serving · cloud AI (Bedrock/Azure/Vertex) · AI security · AI economics.
**Best used for:** design, review, cost, scale, security, build-vs-buy on AI systems.

## agentic-design-patterns
**Purpose:** Map of agentic/LLM-agent design patterns across LangGraph, LangChain, LlamaIndex,
CrewAI, AutoGen, OpenAI Agents SDK, Claude Agent SDK, and the literature.
**Best used for:** understanding the pattern space, not running any one library.

## claude-api **[built-in]**
**Purpose:** Reference for Claude API / SDK — model ids, pricing, params, streaming, tool use, MCP,
caching, migration. **Read before** answering anything about Claude/Anthropic models from memory.

## skill-creator **[built-in]**
**Purpose:** Create, edit, optimize and eval skills. **This is sagent's hands** for §5.

## Code quality **[built-in]**
`code-review` · `security-review` · `simplify` · `run` · `init` · `workflow-authoring`

## Harness config **[built-in]**
`update-config` (settings.json, hooks, permissions) · `keybindings-help` · `fewer-permission-prompts` ·
`loop` · `schedule`
**Known constraint:** `schedule` and `CronCreate` are unusable in this environment — use Windows
Task Scheduler.

---

# DOMAIN: Jyotish (firewalled)

## jyotish-reader
**Purpose:** South Indian Vedic astrology chart reader. Two modes: Full Reading and Ashtakavarga.
**Explicitly invoked only.**
**Charts on file:** Sai (the user) · Veena (wife) · Prianka (daughter) · Raja · MadhuKrishna ·
Jayant + wife + two children.
**Hard rules (from user memory):** chart analysis ONLY — no career/financial/medical strategy, no
naming real people to act on; every forward-looking window must cite historical analogues; ask when
birth data is missing.

## d1-image-to-text
**Purpose:** Convert a South Indian D1 chart IMAGE into the plain-text format jyotish-reader consumes.
**Feeds:** jyotish-reader.

**FIREWALL:** these conventions never cross into trading, career or research work, and those
domains' conventions never cross into here.

---

# DOMAIN: Language & Content

## smob-dic
**Purpose:** Vocabulary Genius — words, etymology, nuance, word games, communication coaching, for
any age group.
**Related project:** Prianka's daily TikTok 5-word series (check the used/rejected list first;
audience is 18-25 and NOT techie).

---

# DOMAIN: Home & Property

## shandy-man
**Purpose:** DFW/North Texas residential handyman, repair diagnostician and contractor-quote
auditor. Works FOR the homeowner, not for the contractor.
**Capabilities:** Diagnose any household failure · repair-vs-replace judgement · DFW-rate pricing
and quote forensics (🟢/🟡/🟠/🔴 with a counteroffer) · part identification from a photo · permit
and licensed-trade determination · HOA vs city-permit distinction · North Texas specialisation
(expansive clay foundations, slab leaks, summer heat and AC, attics, freeze prep and thaw damage,
hail/roofing, brick veneer and weep holes, drainage, irrigation, hard water, garage doors, pests,
UV-degraded exterior caulk).
**Inputs:** Symptom description, photos (wide + close + model plate), any contractor quote, the
city. **Default location: Plano, TX** — confirm when permits or pricing matter.
**Outputs:** Diagnosis · cheapest-first check · fix steps · parts/tools · DIY-or-hire with
difficulty · DFW price bands · quote verdict.
**Key rules:** Never diagnose foundation failure from a crack — recommend an *independent*
structural engineer, not the company selling piers. Never advise skipping a required permit.
Never seal weep holes or vents. Torsion springs go to a pro. Always run the "Don't Replace It
Yet" challenge before endorsing a replacement.
**Note:** Permit rules differ between adjacent DFW cities and change — the skill verifies the
specific city's current rule by web check (2–3 searches) rather than asserting from memory.
**Persistent state:** `C:\Users\ssair\house\` — `HOUSE.md` (source of truth: property facts,
equipment register with install dates and warranty status, open items, vendors, seasonal
calendar) and `house-log.md` (every query with its outcome). **Read-before / write-after is
mandatory**, per SKILL.md §0. Catches warranty windows, detects recurrences, and builds the
written history that defeats an upsell.
**Related:** none — this is a standalone domain.

---

# DOMAIN: Documents & Output

| Skill | Purpose |
|---|---|
| `docx` **[built-in]** | Word documents |
| `xlsx` **[built-in]** | Spreadsheets (.xlsx/.xlsm/.csv/.tsv) |
| `pptx` **[built-in]** | Slide decks |
| `pdf` **[built-in]** | PDF read/edit/create/OCR |
| `dataviz` **[built-in]** | **Read before writing ANY chart code**, in any medium |
| `design` **[built-in]** | Multi-artboard visual design canvas |
| `artifact-design` **[built-in]** | **Read before writing any artifact** |
| `artifact-diagramming` **[built-in]** | Diagrams inside artifacts |
| `artifact-capabilities` **[built-in]** | Runtime capabilities for published artifacts |

---

# DOMAIN: System / Memory

| Skill | Purpose |
|---|---|
| `consolidate-memory` **[built-in]** | Merge duplicates, fix stale facts, prune the memory index |
| `setup-cowork` / `create-cowork-plugin` / `cowork-plugin-customizer` **[built-in]** | Cowork plugin lifecycle |
| `claude-code-guide` (agent) | Questions about Claude Code, Agent SDK, Claude API, Claude in Slack |

**User auto-memory:** `C:\Users\ssair\.claude\projects\C--Users-ssair\memory\` with `MEMORY.md` as
the index. This is the durable store; `sagent/memory/` holds routing-specific state only.

---

# Tools & external capabilities

* **MCP (via claude.ai):** Gmail *(draft-only — CANNOT send)* · Google Drive · Intuit TurboTax.
* **Data:** Postgres `trading` on `localhost:5433` (PG18) — all 11 former SQLite DBs consolidated ·
  Polygon/Massive API (history from 2003-09-10; news + `insights` sentiment + options IV/greeks
  entitled; indices 403) · `C:\Users\ssair\s&p Historic Data\` point-in-time membership 1996-2026.
* **Generic agents:** `Explore` (read-only fan-out search) · `Plan` (implementation design) ·
  `general-purpose` · `claude` · `statusline-setup`.
* **Deferred tools** (load via `ToolSearch`): WebSearch · WebFetch · Monitor · SendMessage ·
  SendUserFile · Cron* · PushNotification · NotebookEdit · plan-mode tools.

---

# Known gaps (candidates, not commitments)

| Gap | Level | Note |
|---|---|---|
| Goal tracking / decision journal across sessions | 3 | Partly covered by `sagent/memory/` — watch whether it earns core status |
| Contradiction detection across memory files | 3 | Memory index is large; stale facts have bitten before |
| Travel planning | 2 | No skill exists; only build on repeat demand |
| Health / medical research | 2 | No skill; note the jyotish firewall applies |

Do not build any of these speculatively. Wait for the second real request.
