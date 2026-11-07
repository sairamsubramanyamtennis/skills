# Agent & LLM security — threat model and review checklist

Read whenever the design includes an agent with tools, an MCP server, or retrieval over content the
system does not control.

**Founding principle:** an agent that can execute actions is a **security principal**. It gets an
identity, an enumerated permission set, an audit trail, and a blast radius you have bounded on
purpose. Not "the LLM calls a function."

## The core asymmetry

There is no reliable, general defense against prompt injection. Instruction and data share one
channel; the model cannot definitively tell them apart. Every mitigation below is
probability-reduction, not elimination. **Architect so that a successful injection is survivable**,
because eventually one succeeds.

This is the single most common design error in the field: treating injection as an accuracy problem
to be solved with a better system prompt, rather than an authorization problem to be solved with
scoped permissions.

## The lethal trifecta

An agent is exfiltration-capable when it combines all three:

1. **Access to private data** — files, DB, email, internal APIs, secrets.
2. **Exposure to untrusted content** — web pages, PDFs, tickets, emails, user uploads, retrieved
   documents, third-party MCP servers, tool *outputs*, subagent results.
3. **An outbound channel** — network calls, writes to shared surfaces, rendered images/links,
   sending messages, even a verbose error path.

**Break at least one leg, or accept the risk explicitly and in writing.** Most real deployments
break leg 3 (egress allowlist, no image/link rendering from model output) or leg 1 (per-user scoped
credentials so the blast radius is the user's own data, which they already had).

## Threat catalog

| Threat | Mechanism | Primary mitigation |
|---|---|---|
| **Direct prompt injection** | User overrides system instructions | Never rely on prompt-level control for authorization; enforce in code |
| **Indirect prompt injection** | Instructions hidden in retrieved/fetched content | Treat all tool output as untrusted data; break the trifecta |
| **Data exfiltration** | Injected instruction sends data out via URL, image, tool call | Egress allowlist; strip/deny markdown images and auto-links; no arbitrary URL fetch |
| **Tool poisoning** | Malicious MCP tool *description* carries instructions | Pin and review server versions; diff descriptions on update; allowlist servers |
| **Rug-pull / supply chain** | Approved MCP server or model changes behavior after approval | Version pinning, integrity checks, change detection, vendored copies |
| **Confused deputy** | Agent uses its own broad credentials for a user's narrow request | Per-user scoped credentials; propagate the caller's identity, never a service superuser |
| **Excessive agency** | Agent has tools it doesn't need for the task | Least privilege per task, not per application; separate read and write agents |
| **RAG poisoning** | Attacker-controlled documents enter the index | Provenance and trust tiers on the corpus; restrict who can write to it; treat retrieved text as data |
| **Memory poisoning** | Injected content persists into long-term agent memory and reactivates later | Validate on write, not just read; scope memory per user; expiry; never store raw untrusted text as instruction-shaped memory |
| **Secrets in context** | Keys in prompts, env, or tool output; leaked via output or logs | Broker credentials outside the model; the agent gets a handle, never the secret |
| **Sandbox escape / RCE** | Code-execution tool | Container/microVM isolation, no host mount, no credentials in env, network off by default, CPU/mem/time caps |
| **Insecure output handling** | Model output passed to a shell, SQL, `eval`, or a browser | Treat output as untrusted input to the next system: parameterize, escape, validate |
| **Denial of wallet** | Unbounded loops, recursive agents, huge contexts | Hard caps on turns, tokens, tool calls, spend per request and per tenant |
| **Model supply chain** | Tampered weights, malicious pickle, typosquatted model repo | Safetensors, checksum verification, trusted registries, scan artifacts |
| **PII/regulated leakage** | Sensitive data to a provider that retains or trains on it | Verify retention terms per SKU; redact pre-send; regional/private deployment |

## Design review checklist

Work through these on any agentic design:

**Identity & permissions**
- [ ] Does the agent have its own identity, distinct from the user and from the service?
- [ ] Is every tool's authorization enforced **in the tool implementation**, not in the prompt?
- [ ] Are credentials scoped to the *caller*, so the agent can never exceed what that user could do?
- [ ] Least privilege per task — are read-only paths actually read-only?
- [ ] Which actions require human approval, and is that gate enforced server-side?

**Trust boundaries**
- [ ] Draw them. Which content is trusted, which is not, and where does untrusted content enter?
- [ ] Is tool output treated as untrusted? (It usually is not — this is the common gap.)
- [ ] Are subagent results and MCP server responses on the untrusted side? (They should be.)

**Trifecta**
- [ ] Private data + untrusted content + egress — which leg is broken, and how?
- [ ] Can the model cause an outbound request with attacker-influenced content? Include rendered
      markdown images, links, webhooks, and error messages.

**Containment**
- [ ] Sandboxing for any code execution: isolation type, network policy, filesystem, resource caps.
- [ ] Blast radius if the agent is fully adversarial for one request — write it down explicitly.
- [ ] Reversibility: what can it do that cannot be undone? Are those actions gated?

**Limits & observability**
- [ ] Caps: max turns, max tool calls, max tokens, max spend, wall-clock timeout.
- [ ] Full audit log: every tool call with arguments, caller identity, and result, retained.
- [ ] Alerting on anomalous tool-call patterns, spend spikes, and repeated failures.
- [ ] Can you reconstruct exactly what happened in a given run, months later?

**MCP specifically**
- [ ] Server allowlist; who approved each server and when.
- [ ] Version pinning and change detection on tool *descriptions*, not just code.
- [ ] Authentication to the server, and what identity the server acts as downstream.
- [ ] Is the server itself in your trust boundary or someone else's infrastructure?

**Data & compliance**
- [ ] PII/regulated data classification for everything that reaches a model provider.
- [ ] Provider retention and training terms for the specific SKU and region in use.
- [ ] Data residency: where does inference physically happen?
- [ ] Redaction/tokenization before send, where required.

**Guardrails** (defense in depth, never the primary control)
- [ ] Input and output filtering, injection classifiers, PII detection, topic constraints.
- [ ] Understand their false-positive/negative rates. They reduce probability; they do not authorize.

## Sarch's standing verdicts

- **A guardrail model is not an authorization boundary.** Anything a determined adversary can talk
  past is a speed bump. Put the boundary in code with real credentials.
- **"Human in the loop" degrades to rubber-stamping** at any real volume. Gate the small number of
  irreversible/high-value actions and make those approvals informative — show the diff, the target,
  the amount. Approving 200 identical dialogs a day is not a control.
- **Multi-agent expands the attack surface faster than the capability.** Every agent boundary is a
  new untrusted channel. Justify each additional agent on security grounds as well as capability.
- **The read-only agent is the underrated design.** An enormous fraction of enterprise value is
  available from agents that can only read and propose. Ship that first; add write capability
  deliberately, tool by tool.
