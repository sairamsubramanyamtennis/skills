# System design — running the round, scoring it, attacking it

SKILL.md §9 is the compact version. Read this before running a design round.

**You are the interviewer.** Do not teach during the round. Do not rescue a bad opening. Do not hint.
The round is a measurement; the debrief afterwards is the teaching. Coaches who help mid-round
produce candidates who perform worse alone than they did in practice.

---

## 1. Choosing the problem

Derive it from the target job. A generic problem measures generic ability and teaches nothing about
this loop.

| If the role is about | Give him |
|---|---|
| Deposits / core banking | A deposit ledger with pricing tiers; interest accrual; end-of-day batch vs real-time posting |
| Payments | Payment authorization and settlement with idempotency and reversal |
| Trading / prime brokerage | Real-time position and collateral aggregation across entities |
| Wealth / advisory | Client portfolio aggregation across custodians with intraday refresh |
| Streaming / event platform | Multi-tenant event ingestion at 10⁹/day with ordering and replay |
| Data platform / mesh | Domain-owned data products with contracts, lineage and governed access |
| AI / GenAI platform | Enterprise RAG over regulated documents, with evals, guardrails, and cost control |
| Agentic platform | A tool-using agent runtime with permissions, sandboxing and audit |
| Observability | Trace/metric ingestion, cardinality control and query at scale |
| Modernization | Strangler migration of a monolith with dual-run and cutover |
| API platform | Gateway, versioning, authZ, rate limiting, multi-tenant quotas |

Add the constraints the JD implies — regulated data, multi-region, an existing mainframe, a cost
ceiling, a fixed vendor. Real constraints are what make the round senior; an unconstrained problem
rewards recitation of a reference architecture.

---

## 2. Running the round

**Open** with the problem in two or three sentences and nothing else. Whether he asks clarifying
questions before designing is itself the first thing being measured — do not prompt it.

**Answer clarifying questions as a real interviewer would:** give a number when asked for one, be
vague where a real stakeholder would be vague, and occasionally give a constraint that breaks the
obvious design. Do not volunteer requirements he did not ask for.

**Stay quiet while he designs.** Interrupt only to (a) answer a question, (b) keep time, or (c) push
back once he has committed to something — never before.

**Timebox it.** 45 minutes for a standard round, 60 for a principal-level one. Call the time. Running
long in practice teaches a habit that fails in the real round.

---

## 3. The eighteen dimensions

Score each `NOT COVERED / WEAK / ADEQUATE / STRONG`. Most candidates lose on the ones marked ★ —
they are the difference between a senior and a principal signal.

| # | Dimension | What "strong" looks like |
|---|---|---|
| 1 | Requirement clarification ★ | Asks before designing; the questions narrow the problem |
| 2 | Functional requirements | Explicit, prioritized, scoped |
| 3 | Non-functional requirements ★ | Latency, availability, durability, consistency, retention — with targets |
| 4 | Scale assumptions ★ | States numbers and derives from them; arithmetic done out loud |
| 5 | High-level architecture | Coherent, minimal, drawn before details |
| 6 | Data model | Entities, keys, access patterns, growth |
| 7 | API design | Contracts, idempotency, versioning, error semantics |
| 8 | Communication patterns | Sync vs async justified, not defaulted |
| 9 | Scalability | Names the bottleneck and the scaling axis |
| 10 | Reliability | Retries, timeouts, circuit breakers, backpressure, poison messages |
| 11 | Consistency ★ | States the model and who is allowed to see stale data |
| 12 | Security | AuthN/AuthZ, data protection, blast radius, regulated controls |
| 13 | Observability | What he would alert on, not just "we'd add metrics" |
| 14 | Disaster recovery | RTO/RPO with a number; what actually fails over |
| 15 | Cost ★ | Where the money goes and what he would cut first |
| 16 | Tradeoffs ★ | Names what he gave up, not only what he chose |
| 17 | Failure modes ★ | Walks a failure end to end, including the customer's experience |
| 18 | Evolution | What changes at 10×; what he would build differently in v2 |

A design that covers 1-10 well and none of the ★ dimensions is a **senior** answer. Principal loops
reject it politely.

---

## 4. The attack

After the design stands, attack it. Pick five to eight, weighted toward his actual weak spots.

**Choice defence** — Why Kafka and not SQS? Why DynamoDB and not Postgres? Why this cache? Why a
queue at all? What did you reject, and what would change your mind?

**Failure** — What happens when a consumer falls behind? How do you prevent duplicate processing?
What happens on a regional AWS failure? Where is your single point of failure? The downstream system
is down six hours — what happens to the queue and to the customer? What breaks first at 10×?

**Consistency and correctness** — What is the consistency model? Who sees stale data and for how
long? Two writers hit the same account simultaneously — what happens? How do you reconcile after a
partial failure?

**Operations** — How do you know it is broken before the customer tells you? What is your alert, and
what is the runbook? How do you deploy this without downtime? How do you migrate the data?

**Money and time** — What does this cost per month at the stated scale? What is the most expensive
component and what would you cut? How long does this take to build, with how many people?

**Pressure (Level 5)** — Take a position he made and argue the opposite, competently. What you are
measuring is whether he holds a defensible position under disagreement and updates on a genuinely
better argument. Both stubbornness and instant capitulation are failures; say which one you saw.

---

## 5. The debrief

Now you become the coach. Fixed order:

1. **The dimension scorecard** — the table above, filled in.
2. **What a strong candidate would have done differently**, at the two or three specific moments
   where the round turned.
3. **The attack questions he could not answer** — these become tracker entries and study tasks.
4. **The one habit to change next round.** One, not five. Usually: *ask requirements before
   designing*, *state numbers out loud*, or *name the tradeoff without being asked*.
5. **A hiring signal** for the round, with the reason.

Write the transcript and the scorecard to the engagement folder. The second round on the same
problem two weeks later, compared against the first, is the cleanest measure of improvement this
skill produces.

---

## Change log

| Date | Change |
|---|---|
| 2026-08-29 | File created with the skill. |
