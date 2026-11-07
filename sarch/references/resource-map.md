# Living AI resource map

**Purpose:** a dated map of where authoritative information lives, plus whatever has actually been
verified and when. This file is *where to look* first, *what we found* second.

**Seeded 2026-08-09.** The URLs below are the canonical documentation entry points. **No value in
the "verified findings" tables has been fetched yet** — they start empty by design, so nothing here
can be mistaken for a current fact.

## How to use and maintain this file

- **Read before answering** anything in volatile territory.
- **Cadence** governs trust. An entry older than its cadence is a lead, not a fact — re-verify.
- **Write back after every verification**: value, as-of date, source URL, confidence.
- **Confidence markers**: `[verified]` fetched from a primary source on the stated date ·
  `[secondary]` from an aggregator or non-primary source · `[stale]` past cadence, re-check ·
  `[unverified]` never checked.
- Prune aggressively. A long map nobody reads is worse than a short one that is trusted.

| Area | Refresh cadence |
|---|---|
| Model lineups, pricing, context limits | Every use, or ≤ 30 days |
| Cloud AI service features and availability | ≤ 60 days |
| Frameworks, SDKs, MCP ecosystem | ≤ 60 days |
| GPU / accelerator specs and instance pricing | ≤ 90 days |
| Benchmarks and leaderboards | Every use (they move) |
| Research, standards, security guidance | ≤ 180 days |

---

## 1. Model providers

Canonical docs and pricing entry points. **Fetch before quoting anything.**

| Provider | Docs | Pricing / models |
|---|---|---|
| Anthropic | docs.claude.com · docs.anthropic.com | anthropic.com/pricing — **but use the `claude-api` skill as the authority** |
| OpenAI | platform.openai.com/docs | openai.com/api/pricing · platform.openai.com/docs/models |
| Google (Gemini API) | ai.google.dev/gemini-api/docs | ai.google.dev/pricing |
| Google (Vertex AI) | cloud.google.com/vertex-ai/docs | cloud.google.com/vertex-ai/generative-ai/pricing |
| Meta (Llama) | llama.com/docs · huggingface.co/meta-llama | Open weights — check licence terms per model |
| Mistral | docs.mistral.ai | mistral.ai/pricing |
| xAI | docs.x.ai | docs.x.ai/docs/models |
| Cohere | docs.cohere.com | cohere.com/pricing |
| DeepSeek | api-docs.deepseek.com | api-docs.deepseek.com/quick_start/pricing |
| Alibaba / Qwen | qwenlm.github.io · help.aliyun.com (DashScope) | Open weights + API tiers |
| Microsoft (Phi) | huggingface.co/microsoft · azure.microsoft.com/products/ai-foundry | Via Azure AI Foundry |
| Amazon (Nova/Titan) | docs.aws.amazon.com/nova | aws.amazon.com/bedrock/pricing |
| NVIDIA (NIM/Nemotron) | docs.nvidia.com/nim · build.nvidia.com | build.nvidia.com |
| Hugging Face | huggingface.co/docs | huggingface.co/pricing |

**Verified findings** — *(model, context, modality, price in/out, as-of, source, confidence)*

_(empty — populate on first verification)_

## 2. Agent ecosystem

| Thing | Where |
|---|---|
| MCP specification | modelcontextprotocol.io/specification |
| MCP docs + SDKs | modelcontextprotocol.io · github.com/modelcontextprotocol |
| Claude Agent SDK | See the `claude-api` skill |
| OpenAI Agents SDK | openai.github.io/openai-agents-python · platform.openai.com/docs/guides/agents |
| LangGraph | langchain-ai.github.io/langgraph · github.com/langchain-ai/langgraph |
| LangChain | python.langchain.com/docs |
| LlamaIndex | docs.llamaindex.ai |
| Semantic Kernel | learn.microsoft.com/semantic-kernel |
| AutoGen | microsoft.github.io/autogen |
| CrewAI | docs.crewai.com |
| Pydantic AI | ai.pydantic.dev |
| AWS Bedrock Agents / AgentCore | docs.aws.amazon.com/bedrock |
| Vertex AI Agent Builder / ADK | cloud.google.com/products/agent-builder · google.github.io/adk-docs |
| Azure AI Foundry Agent Service | learn.microsoft.com/azure/ai-foundry |
| Coding agents | Claude Code (claude.com/claude-code, and the `claude-code-guide` agent) · GitHub Copilot (docs.github.com/copilot) · OpenAI Codex (platform.openai.com/docs) · Cursor · Aider |

**Pattern taxonomy lives in the `agentic-design-patterns` skill — do not duplicate it here.**

**Verified findings** — *(component, version, maturity note, as-of, source)*

| Component | Finding | As-of | Source | Confidence |
|---|---|---|---|---|
| **MCP governance** | Anthropic **donated MCP to the Agentic AI Foundation (AAIF) in Dec 2025**. Now a vendor-neutral standard under community governance (Working Groups, SEPs), not one vendor's product decision. Current spec revision **2026-07-28**. | 2026-08-30 | blog.modelcontextprotocol.io/posts/2026-mcp-roadmap · /posts/2026-07-28 | `[secondary]` — project blog, not the spec page itself |
| **MCP adoption** | ~97M monthly SDK downloads · 9,400+ public servers · native support from Anthropic, OpenAI, Google DeepMind, Microsoft. **~41% of surveyed software orgs in limited or broad production**; Fortune 500 implementation reported ~**28%** inside 18 months. | 2026-08-30 | Industry surveys (MCP Institute "State of MCP 2026", cdata, digitalapplied) | `[secondary]` — vendor/aggregator surveys, methodology unverified. Directionally right; do not quote as precise. |
| **MCP security gap — the number that matters** | **Only ~8.5% of public MCP servers implement the spec's mandatory OAuth 2.1.** Security is the reported leading blocker to enterprise deployment. 2026 roadmap priorities: transport scalability, agent communication, governance, enterprise readiness. | 2026-08-30 | Same survey set + MCP 2026 roadmap | `[secondary]` — **the single most useful MCP fact for a regulated-enterprise conversation**: adoption has badly outrun security maturity |
| **Istio ambient mode** | Sidecar-less data plane (per-node `ztunnel` + optional waypoint proxies) **GA since Nov 2024**; removes the per-pod sidecar overhead that was the main adoption blocker. Reported ~75% `ztunnel` perf improvement over four releases. Project roadmap priority is a supported sidecar→ambient migration, namespace by namespace. | 2026-08-30 | InfoQ, Solo.io, AWS containers blog, CloudNativeNow | `[secondary]` — vendor/press, not istio.io docs. Re-verify against istio.io before quoting the 75%. |
| **Istio @ KubeCon 2026 (Amsterdam)** | Announced **ambient multicluster**, **Gateway API Inference Extension**, experimental **agentgateway** support — i.e. the mesh is being positioned for AI/inference traffic. | 2026-08-30 | InfoQ 2026/04 | `[secondary]` |
| **EKS + mesh** | Istio installable as an **EKS add-on**, supporting both sidecar and ambient modes; **EKS Auto Mode** (automated node provisioning/scaling) documented working alongside ambient mesh. | 2026-08-30 | aws.amazon.com/blogs/containers · docs.solo.io | `[secondary]` — AWS blog is near-primary; feature availability may have moved |

**Cadence note.** MCP adoption figures move fast — treat anything here as a lead after ~30 days. The
*governance* fact (AAIF donation) and the *ambient GA* fact are structural and age slowly; the
percentages are the volatile part.

## 3. RAG / data layer

| Category | Options and docs |
|---|---|
| Vector DBs (dedicated) | Pinecone (docs.pinecone.io) · Weaviate (weaviate.io/developers) · Qdrant (qdrant.tech/documentation) · Milvus (milvus.io/docs) · Chroma (docs.trychroma.com) |
| Vector-in-your-existing-DB | **pgvector** (github.com/pgvector/pgvector) · pgvectorscale · Elasticsearch/OpenSearch kNN · Redis · MongoDB Atlas Vector · SQL Server / Oracle vector types |
| Search engines | OpenSearch (opensearch.org/docs) · Elasticsearch · Vespa (docs.vespa.ai) · Typesense · Lucene/Tantivy · BM25 baselines |
| Managed RAG | AWS Bedrock Knowledge Bases · Vertex AI Search · Azure AI Search (learn.microsoft.com/azure/search) |
| Embeddings | OpenAI · Cohere Embed · Voyage · Google · BGE / E5 / GTE / Nomic (open) — leaderboard: huggingface.co/spaces/mteb/leaderboard |
| Rerankers | Cohere Rerank · Voyage rerank · BGE-reranker · cross-encoder families |
| Knowledge graphs / GraphRAG | Neo4j (neo4j.com/docs) · Microsoft GraphRAG (microsoft.github.io/graphrag) · LightRAG |
| Parsing / ingestion | Unstructured · LlamaParse · Docling · Azure Document Intelligence · AWS Textract |
| Eval | RAGAS (docs.ragas.io) · TruLens · DeepEval · promptfoo · Braintrust · LangSmith · Arize Phoenix |

**Sarch's standing prior:** for most enterprise workloads under ~10M chunks, **pgvector on the
Postgres you already run** beats a dedicated vector DB on total cost of ownership, and hybrid
BM25 + dense with a reranker beats pure dense retrieval. Make the case for anything more.

**Verified findings**

| Thing | Finding | As-of | Source | Confidence |
| **Kafka 4.0** | Released **March 2025**. **ZooKeeper removed entirely — KRaft is the only metadata mode**, consensus built on Kafka's own log. **KIP-932 "share groups"** shipped in preview: queue-like cooperative consumption independent of partition count, with per-message ack and redelivery. Faster rebalances. | 2026-08-30 | kafka.apache.org release announcement + Confluent blog + secondary write-ups | `[secondary]` — the Apache announcement is primary but was read via aggregators |
| **Kafka tiered storage (KIP-405)** | Decouples compute from storage: brokers offload older log segments to object storage (S3/GCS/Azure Blob). Makes long/indefinite retention economical and shrinks broker disk. | 2026-08-30 | Same set | `[secondary]` — relevant to regulated retention obligations |
| **Open table formats — the question is settled** | **Apache Iceberg won.** Snowflake, AWS, Google and the OSS ecosystem converged on it as the neutral standard. **Iceberg v3 GA** across Snowflake, Databricks and Amazon S3 Tables. Databricks has proposed **Delta 5.0 adopt Iceberg v4's adaptive metadata-tree structure** — one shared metadata layout. **Delta UniForm** already exposes Delta tables as Iceberg to Snowflake, BigQuery, Trino, Dremio from one Parquet copy. | 2026-08-30 | Databricks blog, Snowflake blog, dev.to catalog survey, The Register | `[secondary]` — vendor-authored and opinionated. Directionally strong consensus; verify specific version claims before quoting |
| **Where the lock-in moved** | With the format neutral, the meaningful lock-in is now the **catalog and governance layer**, not the file format. The 2026 question is "which catalog do you commit to", not "which format". | 2026-08-30 | Same set | `[secondary]` — **the most useful single framing in this area** |
| **Data mesh — the 2026 verdict** | Peak hype **2022** → trough of disillusionment **2024** → by 2026 most orgs **kept domain ownership, data-as-product and federated standards, and dropped the dogma**. Reported **only ~18% of orgs have the governance maturity** to adopt successfully; missing any of four preconditions (product-engineering culture, skills, platform investment, governance with teeth) → **re-centralises within ~18 months or stalls**. Consensus shape: **mesh for organisational design, fabric for technical plumbing.** | 2026-08-30 | Thoughtworks 2026 state-of-data-mesh retrospective + corroborating analyses | `[secondary]` — Thoughtworks originated the concept, so treat their retrospective as informed but not disinterested |
| **Data mesh — named failure modes** | (1) Datasets **relabelled** "data products" with no SLA/versioning/consumer support — the dominant failure. (2) **Metric fragmentation** without federated governance — one documented case reported **16 competing CLV metrics**. (3) **Over-engineering** — mesh across 5 domains where a governed central lakehouse would have served 3 more years at a fraction of cost. (4) Governance as a committee rather than automated pipeline checks. | 2026-08-30 | Same set | `[secondary]` — **use these to hold a nuanced position; data mesh is contested and evangelising it is a credibility risk with a sceptical audience** |
|---|---|---|---|---|
| NotebookLM / "Gemini Notebook" — consumer | **No public API.** No self-serve key, no supported endpoint. Access is UI + manual export only. | 2026-08-09 | Multiple secondary (autocontentapi, web-clipper blogs); no Google consumer API doc exists | `[secondary]` |
| Gemini Notebook **Enterprise** API | Real, but **Preview / `v1alpha`**, not GA. `notebooks.create/get/listRecentlyViewed/batchDelete/share` on `https://{us\|eu\|global}-discoveryengine.googleapis.com/v1alpha/projects/{PROJECT_NUMBER}/locations/{LOC}/notebooks`. OAuth2 bearer (`gcloud auth print-access-token`). Requires a GCP project + Gemini Enterprise licences + `Cloud NotebookLM User` IAM role. Sits under Gemini Enterprise / Agentspace; supports VPC-SC + CMEK. | 2026-08-09 (doc page updated 2026-08-03) | docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks | `[verified]` |
| Colab notebooks | Plain `.ipynb` in Drive (`application/vnd.google.colaboratory`) — fully reachable via the ordinary Drive API/MCP. No special API needed. | 2026-08-09 | Drive MIME conventions | `[verified]` |

**Sarch's position:** NotebookLM is a *read surface*, not a system of record. Never let it be the only
place a corpus lives. Keep source-of-record in Drive/filesystem/Postgres and treat NotebookLM as a
downstream view. Third-party "NotebookLM API" scrapers work by replaying Google session cookies —
disqualifying for any account touching regulated or employer data.

## 4. Infrastructure

| Category | Where |
|---|---|
| NVIDIA GPUs | docs.nvidia.com · developer.nvidia.com — datasheets for H100/H200/B200/GB200 generations |
| TPUs | cloud.google.com/tpu/docs |
| AWS silicon | aws.amazon.com/machine-learning/trainium · /inferentia · awsdocs-neuron.readthedocs-hosted.com |
| AMD | rocm.docs.amd.com |
| Inference engines | vLLM (docs.vllm.ai) · TensorRT-LLM (nvidia.github.io/TensorRT-LLM) · SGLang (docs.sglang.ai) · llama.cpp · Ollama · TGI (huggingface.co/docs/text-generation-inference) |
| Serving / orchestration | Ray Serve (docs.ray.io) · KServe · NVIDIA Triton · Kubernetes device plugin, MIG, time-slicing · Karpenter for GPU nodes |
| Fine-tuning | PEFT (huggingface.co/docs/peft) · TRL · Axolotl · Unsloth · LLaMA-Factory · torchtune |
| Quantization | GPTQ · AWQ · GGUF · bitsandbytes · FP8 (Transformer Engine) · SmoothQuant |
| Observability | OpenTelemetry GenAI semantic conventions · LangSmith · Langfuse · Arize · Datadog LLM Observability |

**Verified findings** — *(chip, HBM, bandwidth, FLOPS, instance type, $/hr, as-of, source)*

### 4a. The 2026 memory crisis — read this before recommending ANY on-prem/home hardware

**Standing context (as-of 2026-08-10, `[secondary]`, cadence 30 days — this moves fast).** HBM
allocation for datacenter AI has starved GDDR7 and LPDDR5X supply. Every memory-heavy consumer and
workstation SKU is trading 1.5–2.5× above its launch price, and vendors are *deleting* high-memory
configurations rather than raising prices. **Any $/GB figure from before 2026 is worthless.**

| Part | Memory / BW | Launch price | Aug-2026 street | Note |
|---|---|---|---|---|
| RTX 5090 | 32 GB GDDR7 · 1,792 GB/s | $1,999 MSRP (Jan-2025) | **~$4,300–5,000** (NVIDIA's own store listed $4,929.99 on 2026-08-05) | VRAM alone ≈ $820 of BOM |
| RTX PRO 6000 Blackwell WS | 96 GB GDDR7 ECC · ~1,792 GB/s · 24,064 CUDA · 600 W | $8,565 (Mar-2025) | **$13,250** on NVIDIA Marketplace (+55% in ~16 mo) | Largest VRAM on any discrete card |
| NVIDIA DGX Spark (GB10) | 128 GB unified · **273 GB/s** | announced $3,000 | **~$4,679–4,699** | Reviews converge on "CUDA-native prototyping sandbox, not inference infra" |
| Mac Studio M3 Ultra | max **96 GB** (819 GB/s class) | 512 GB option was +$4,000 | **~$5,299** base `[secondary]`; 256 GB and 512 GB SKUs **pulled by Apple** (Tom's Hardware, MacDailyNews) | Apple store fetch on 2026-08-10 rendered only M3 Ultra 28c/60c **96 GB** and M4 Max 36 GB, with no full spec sheet — "96 GB is the ceiling" is corroborated by Tom's Hardware but is an **inference from a partial page**, not a verified config list |
| Mac Studio M4 Max | 36 GB base, ≤128 GB class | $2,499 | $2,499+ | — |
| AMD Ryzen AI Max+ 395 "Strix Halo" | 128 GB LPDDR5X-8000 · **256 GB/s** · 40 CU RDNA3.5 | $1,499–1,999 (early 2026) | **~$2,600** cheapest of 21 Amazon 128 GB listings (2026-07-31); AMD's own dev kit $3,999 | Best $/GB of fast-ish memory that still exists |

**Timing note:** Mac Studio M5 Max / M5 Ultra refresh is reported for **~Oct 2026** (Bloomberg via
MacRumors/Macworld), delayed from earlier in 2026 *because of* memory supply. M5 Ultra tested up to
768 GB internally; shipping that config is doubtful. Do not buy a Mac Studio in Aug–Sep 2026.

### 4b. Local-inference sweet spot for agentic coding (as-of 2026-08-10, `[secondary]`)

| Model | Total / active | Q4 weights | Context | Home-runnable? |
|---|---|---|---|---|
| Qwen3-Coder-Next | 80B MoE / ~3B active (512 experts, 10/tok) | ~46–52 GB | 256K | **Yes** — the only serious agentic coder that fits 128 GB |
| gpt-oss-120b | 120B MoE / ~5.1B active | ~60–70 GB | — | Yes, on 128 GB unified |
| GLM-5.2 (`zai-org/GLM-5.2`, **MIT**, rel. 2026-06-13) | 744B MoE / ~40B active | **~372 GB** | 1M | No (4× PRO 6000 ≈ $53k) |
| Kimi K3 (`moonshotai`, weights 2026-07-27) | 2.8T MoE / **104B active**, 16 of 896 experts/tok, Kimi Delta Attention | **~1.4 TB** | 1M | No |

`[verified]` Qwen3-Coder-Next config from `huggingface.co/Qwen/Qwen3-Coder-Next/config.json`
(2026-08-10): `num_hidden_layers 48`, `num_attention_heads 16`, **`num_key_value_heads 2`**,
`head_dim 256`, `hidden_size 2048`, `num_experts 512`, `num_experts_per_tok 10`,
`max_position_embeddings 262144`, **`full_attention_interval 4`** (hybrid — 12 full-attention layers,
36 linear-attention layers with constant-size recurrent state).

**KV cache is NOT the constraint on this model** — the hybrid layout makes it tiny:

```
Full-attn layers = 48/4 = 12
KV/token/layer   = 2 · H_kv · d_head · b = 2 · 2 · 256 · 2 B = 2 KiB
KV/token         = 12 × 2 KiB = 24 KiB
256K context     = 262,144 × 24 KiB ≈ 6.3 GB      ← vs 43 GB for a dense 70B @ 128k
Linear-layer state = 36 × (32·128·128·2 B) ≈ 36 MiB, constant in T
Total @ 256K     ≈ 48 GB weights + 6.3 GB KV + activations ≈ 56 GB
```

**Doctrine: for agents, prefill is the binding constraint, not decode — and real efficiency is far
below peak.** `[secondary, 2026-08-10]` Measured Strix Halo (Radeon 8060S, **29.70 TFLOPS FP16
peak** per TechPowerUp/topcpu — *not* ~50) does **~340 tok/s prompt processing on gpt-oss-120b**
(kyuz0/amd-strix-halo-toolboxes, visorcraft/strix-halo-llm-perf). Back-solving:
`2 · 5.1e9 · 5e4 = 510 TFLOP ÷ 147 s ⇒ ~3.5 TFLOPS effective ≈ 12% of peak.` **Never assume >15% of
peak FLOPS for llama.cpp/ROCm MoE prefill; ~30–40% is a fair CUDA/vLLM assumption.** A 50k-token cold
agent context therefore costs **1.5–2.5 minutes** on Strix Halo, ~5–8 s on an RTX PRO 6000.

**Decode degrades with context** — at long context KV reads dominate weight reads:
`tok/s ≈ BW / (N_active·b + KV_bytes)`. Qwen3-Coder-Next on Strix Halo (256 GB/s):
~95 tok/s theoretical at 50k ctx, ~33 tok/s at 256k ctx. Model both ends, not just the empty-context
number every benchmark quotes.

**Prefix caching is a precondition, not an optimization.** Append-only agent turns re-prefill only
Δ (~4 s); any cache miss — session start, context compaction, a re-read file — costs the full cold
prefill. See the agent-loop multiplier in `cost-and-capacity-math.md`.

### 4c. Source-quality warning for this section

Most consumer-hardware and local-LLM search traffic in 2026 lands on AI-generated affiliate content
farms (`fungies.io`, `localaimaster.com`, `neuralcoretech.com`, `modelfit.io`, `runaihome.com`,
`whatllm.org`, `llmrun.dev`, `benchlm.ai`, `compute-market.com`, …). They are internally consistent
because they copy each other, which reads as corroboration and is not. **Promote to primary before
asserting:** HF `config.json` for architecture · vendor store/marketplace for price · TechPowerUp /
Tom's Hardware / AnandTech-class outlets for silicon specs · GitHub benchmark repos
(kyuz0/amd-strix-halo-toolboxes, visorcraft/strix-halo-llm-perf) and Level1Techs for measured perf ·
VentureBeat/Fortune/Interconnects-class for release facts. One content-farm claim already surfaced
here was internally contradictory ("Apple released M5 Max Mac Studio" vs Apple's own store).

## 5. Research & benchmarks

| Kind | Where |
|---|---|
| Papers | arxiv.org (cs.CL, cs.LG, cs.AI) · paperswithcode-style trackers · Semantic Scholar |
| Leaderboards | LMArena (lmarena.ai) · Artificial Analysis (artificialanalysis.ai) · HF Open LLM Leaderboard · MTEB |
| Coding | SWE-bench (swebench.com) · SWE-bench Verified · LiveCodeBench · Aider polyglot |
| Agentic / tool use | GAIA · τ-bench · WebArena · OSWorld · BFCL (Berkeley Function-Calling Leaderboard) |
| Reasoning / knowledge | GPQA · AIME · MMLU-Pro · HLE · ARC-AGI |
| Long context | RULER · needle-in-haystack variants (weak) · LongBench |
| Safety | HarmBench · AgentHarm · purple-teaming suites |

**Benchmark doctrine:** treat every score as contaminated until shown otherwise. Prefer held-out,
independently-run, task-relevant evals — ideally *your own* eval set on *your own* data. A
leaderboard delta under a few points is noise for architecture purposes.

**Verified findings** _(empty)_

**Verified findings**

| Thing | Finding | As-of | Source | Confidence |
|---|---|---|---|---|
| **DORA / State of DevOps 2026 — AI and delivery** | **Throughput and stability are decoupling.** AI coding tools no longer delay delivery (a reversal of earlier findings): reported throughput **+2-18%**, **epics completed per developer +~66%**. But stability lags — **median time in PR review up ~441%** (vs ~91% in the prior dataset) and **~31% more PRs merging with no review at all.** Gains reappear downstream as queued reviews, rework, broken tests and risk reaching production. | 2026-09-02 | TechTarget coverage + practitioner analyses (kodus, faros, getdx) | `[secondary]` — **not read from the primary DORA report.** Verify against dora.dev before quoting the 441% or 66% figures in writing. |
| **Interpretation worth keeping** | **The bottleneck moved from writing code to reviewing and validating it.** Any AI-SDLC programme that scales generation without scaling review, test and verification capacity converts a velocity gain into a quality liability. This is the single most useful framing for "AI-enabled SDLC" conversations in regulated environments. | 2026-09-02 | Derived from the above | `[inference]` — mine, but well-supported by the reported data |
| **Micro-frontends / Module Federation** | Matured into a mainstream option; 2026 direction of travel is Webpack-based federation toward **Native ESM federation** (import maps, top-level await). **Consensus verdict: micro-frontends solve *organizational scale*, not code quality** — the decision should follow team structure and independent-deployment need, not novelty. *"If your monolith is poorly structured, splitting it into multiple apps distributes the chaos."* Teams that cannot agree shared contracts need a monorepo and stricter CI, not federation. | 2026-09-02 | Practitioner write-ups (Medium, dev.to), Fowler's micro-frontends article | `[secondary]` — opinionated practitioner sources; the *verdict* is well-corroborated, the tooling specifics are not |


## 6. Security

| Kind | Where |
|---|---|
| OWASP Top 10 for LLM Applications / GenAI | genai.owasp.org |
| OWASP Agentic Security Initiative | genai.owasp.org (agentic threat taxonomy) |
| NIST AI RMF + Generative AI Profile | nist.gov/itl/ai-risk-management-framework |
| MITRE ATLAS | atlas.mitre.org |
| MCP security guidance | modelcontextprotocol.io/specification (security sections) |
| Prompt-injection research | Ongoing; Simon Willison's writing is the best-maintained practitioner index |
| Cloud guidance | AWS/Azure/GCP generative-AI security whitepapers and well-architected AI lenses |

Working checklist and threat model: **`agent-security.md`** in this folder.

**Verified findings** _(empty)_

---

## Change log

| Date | Change |
|---|---|
| 2026-08-09 | Seeded. Structure and source URLs only; no findings verified. |
| 2026-08-09 | §3: verified NotebookLM / Gemini Notebook API status (consumer = none; Enterprise = Preview v1alpha under Gemini Enterprise). |
| 2026-09-02 | §5: first verified findings — DORA 2026 AI throughput-vs-stability decoupling (and the bottleneck-moved framing), plus the micro-frontends 2026 verdict. All `[secondary]`; DORA primary report NOT read. Verified for RJ interview prep (sinterview-tutor E001). |
| 2026-08-30 | §3: first verified findings — Kafka 4.0 (KRaft-only, KIP-932 share groups, tiered storage), Iceberg convergence and the catalog-is-the-lock-in framing, and the data-mesh 2026 verdict + failure modes. All `[secondary]`. Verified for RJ interview prep (sinterview-tutor E001). |
| 2026-08-30 | §2: first verified findings — MCP governance (AAIF donation Dec-2025, spec 2026-07-28), adoption figures, and the ~8.5% OAuth 2.1 compliance gap; Istio ambient GA + KubeCon 2026 announcements; EKS add-on/Auto Mode. All `[secondary]`. Verified for RJ interview prep (sinterview-tutor E001). |
| 2026-08-10 | §4: added §4a (2026 memory crisis — home/on-prem hardware price table, Apple SKU deletions, Mac Studio M5 timing) and §4b (local agentic-coding model footprints; prefill-not-decode doctrine). All `[secondary]` except the Apple store config. Cadence 30 days. |
