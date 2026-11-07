# Cost & capacity math

The chain: **MODEL → TOKENS → COMPUTE → MEMORY → LATENCY → THROUGHPUT → COST.**

Read before quoting a cost, a latency budget, a GPU sizing, or a self-host-vs-API breakeven. Show
the arithmetic in the answer so the assumptions are auditable.

> **All hardware and price figures below are illustrative anchors for worked examples, not current
> facts.** Re-verify against the vendor before quoting. See `verification-playbook.md`.

## Notation

| Symbol | Meaning |
|---|---|
| `N` | Parameters. For MoE use **active** params for compute, **total** for memory |
| `L` | Transformer layers |
| `H_kv` | Key/value heads (= attention heads for MHA; fewer for GQA; 1 for MQA) |
| `d_head` | Head dimension |
| `b` | Bytes per element (fp16/bf16 = 2, fp8/int8 = 1, int4 = 0.5) |
| `T_in`, `T_out` | Input (prefill) and output (decode) tokens |
| `B` | Batch size / concurrent sequences |
| `BW` | Accelerator memory bandwidth (bytes/s) |

## 1. Tokens

Rough English: **~4 characters ≈ 1 token**, ~0.75 words per token. Code, JSON, and non-Latin scripts
are denser in tokens — 2–4× for CJK, materially worse for base64 or minified payloads. Estimate from
a real tokenizer for anything cost-critical; a 30% error here propagates through every number below.

## 2. Compute

```
Forward pass FLOPs   ≈ 2 · N · T          (2 FLOPs per parameter per token: one multiply, one add)
Training FLOPs       ≈ 6 · N · T          (forward + backward ≈ 3× forward)
Prefill FLOPs        ≈ 2 · N · T_in       — compute-bound, parallel across the sequence
Decode FLOPs/token   ≈ 2 · N              — memory-bound, strictly sequential
```

Attention adds a term quadratic in sequence length that is negligible at short context and dominant
at long context. The practical consequence: **prefill and decode are different workloads with
different bottlenecks**, and any capacity model that treats "tokens" as one unit is wrong.

## 3. Memory

```
Weights   = N · b
KV cache  = 2 · L · H_kv · d_head · b   bytes per token per sequence
Total     ≈ weights + KV + activations + fragmentation   (add ~10–20% overhead)
```

**Worked example — a 70B-class model, L=80, H_kv=8 (GQA), d_head=128, fp16:**

```
KV per token = 2 × 80 × 8 × 128 × 2 B = 327,680 B ≈ 320 KiB
128k context, one sequence = 131,072 × 320 KiB ≈ 43 GB
```

Forty-three gigabytes of KV cache **for a single conversation**. That is the whole reason long
context is expensive, why prefix caching matters so much, and why GQA exists: the same model with
full MHA (H_kv = 64) would need ~2.6 MB/token → **~344 GB** for that one sequence.

Capacity falls straight out of it. On 2× 80 GB accelerators (160 GB) with 140 GB of fp16 weights,
~20 GB remains for KV → **~61k tokens of *total* KV across all concurrent sequences.** Sixty
concurrent 1k-token chats, or one long-context session. This calculation, not a vendor throughput
chart, is what determines your concurrency.

Levers: quantize weights (int8 halves them, int4 quarters them), quantize the KV cache, GQA/MQA
models, shorter contexts, paged attention to kill fragmentation, offload to host memory (slow).

## 4. Latency

```
TTFT  ≈ queue delay + (2 · N · T_in) / effective_FLOPS + network
TPOT  ≈ bytes_read_per_decode_step / BW        (weights + KV read every single token)
E2E   ≈ TTFT + TPOT · T_out
```

**Single-stream decode ceiling** (the number people forget): one sequence must read the entire
weight set per token, so

```
max tok/s per stream = BW / (N · b)
```

70B fp16 = 140 GB of reads per token. At ~3.35 TB/s HBM: `140/3350 ≈ 42 ms/token → ~24 tok/s`. Split
across 2 GPUs tensor-parallel, each reads 70 GB → ~21 ms → ~48 tok/s theoretical, call it 35–40 after
collective-communication overhead. **No amount of batching makes a single stream faster** — batching
buys throughput, not per-user speed, and typically costs a little latency.

Levers on TTFT: prompt/prefix caching (the big one — turns prefill into a cache read), shorter
prompts, chunked prefill, a smaller router model. Levers on TPOT: smaller or quantized model, more
bandwidth, tensor parallelism, speculative decoding (2–3× when the draft model accepts well;
~nothing, plus overhead, when it doesn't).

## 5. Throughput

Decode arithmetic intensity with batch `B` at `b` bytes/param: weights are read once and serve all
`B` sequences, so

```
intensity = 2·N·B / (N·b) = 2B/b  FLOP/byte     → for fp16, simply B
```

Compare to machine balance (`peak FLOPS / BW`). At ~990 TFLOPS bf16 and ~3.35 TB/s, balance is
~295 FLOP/byte → decode stays **memory-bound until batch ≈ 300**. That is why continuous batching is
the single highest-leverage serving optimization: below that batch you are paying for compute you are
not using. KV-cache reads also scale with batch and context, so the real crossover is higher at long
context — and long context is usually where you run out of *memory* first anyway.

**Little's Law** for capacity planning:

```
concurrency = arrival_rate × avg_latency
```

10 req/s at 8 s average → 80 concurrent requests in flight. Size KV memory for that, not for the
average.

## 6. Cost

**API:**
```
cost/request = (T_in·P_in + T_cached·P_cache + T_out·P_out) / 1e6
```
With cache hit rate `h`, effective input price = `h·P_cache + (1−h)·P_in`, plus amortized cache-write
premium. Output tokens are typically several times the input price — **reasoning tokens bill as
output**, which is why a reasoning model on a high-volume path can cost 10× the naive estimate.

**Self-host:**
```
$/1M output tokens = (GPU_$/hr × n_GPUs × 1e6) / (aggregate_tok_per_s × 3600)
```
Example: 2 GPUs at $2.50/hr aggregating 2,000 tok/s → `(2.50×2×1e6)/(2000×3600) ≈ $0.69 per 1M
output tokens`. Compelling against API pricing — **at that utilization.** At 10% utilization it is
$6.90, and you now also own an on-call rotation, capacity planning, model upgrades, and eval
regression. Self-hosting wins on sustained high-volume, stable-model, data-residency, or
fine-tuned-model workloads; it loses on spiky traffic and on wanting the newest frontier model.

**The agent-loop multiplier** — the number most estimates miss. An agent re-sends its growing context
every turn. Over `K` turns with base context `C₀` and `Δ` added per turn:

```
total input tokens ≈ K·C₀ + Δ·K(K+1)/2      — quadratic in turns
```

A 20-turn agent adding 2k tokens/turn on a 5k base sends ~520k input tokens, not 20×5k = 100k. Prefix
caching collapses most of this to cache-read rates and is therefore not an optimization but a
precondition for agent economics. Always model agent cost per *task*, never per *call*.

## 7. Model routing economics

With a small model handling fraction `f` at cost `C_s`, escalating the rest at `C_l`, plus router
cost `C_r`:

```
blended = C_r + f·C_s + (1−f)·(C_s + C_l)     if the small model always runs first
```

The failed-attempt cost is why naive cascading disappoints: you pay twice on every escalation. Routing
pays when `f` is high **and** the router is cheap **and** misroutes are cheap to recover from. It does
not pay when quality is uniformly critical or when the escalation rate is above ~40%. Measure `f`
on real traffic before designing around it — it is almost always worse than the pilot suggested.

## Estimation discipline

1. Show the arithmetic. A number without its derivation cannot be challenged or reused.
2. State every assumption with units — tokens per request, requests per day, cache hit rate, output
   length, utilization.
3. Give a range, not a point. The inputs are uncertain; pretending otherwise is false precision.
4. Sensitivity-test the one or two assumptions that dominate. Usually output-token count, cache hit
   rate, and agent turn count.
5. Cost per **task**, cost per **user per month**, and cost as a **fraction of the value created** —
   those are the numbers a decision gets made on. Cost per million tokens is an input, not an answer.
