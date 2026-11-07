# Tutor method — how to teach so it survives an interview

SKILL.md §8 is the compact version. Read this before a teaching session or a quiz.

Teaching for an interview is not teaching for competence. The target is not "understands Kafka" but
"can hold a position about Kafka while a Principal Engineer pushes back for four minutes." That
changes what you do.

---

## 1. Question design by level

The level is a property of the *question*, not the topic. Same topic, five questions:

| Level | Shape | Example (Kafka) |
|---|---|---|
| **1 Fundamentals** | What is it, why does it exist | "What problem does a partition solve that a queue doesn't?" |
| **2 Applied** | Use it correctly in a concrete case | "Ordering per customer, 50M events/hour. What's your partition key?" |
| **3 Senior** | Choose between options and justify | "Why Kafka here and not SQS or Kinesis? What would make you switch?" |
| **4 Principal** | Failure, scale, cost, evolution | "One customer is 40% of volume. What breaks, when do you notice, and what do you change?" |
| **5 Adversarial** | Defend under pressure | "That rebalance strategy adds operational complexity for a problem you could solve with a bigger box. Convince me." |

**Design Level 4 questions first, then work down.** Level 4 is where the interview is actually
decided; Levels 1-2 exist only to find out whether he can get there. If he clears Level 4 cold, do
not spend a minute on Levels 1-3 — record it and move on.

Good Level 4 questions share a shape: **a specific number, an asymmetry, and a consequence.** "50M
events/hour" (number), "one customer is 40%" (asymmetry), "what breaks and when do you notice"
(consequence). Questions without all three produce recitation.

---

## 2. Detecting "correct but shallow"

The single most important diagnostic. Tells:

- Names the technology but not the mechanism ("Kafka handles that").
- Correct at the level of a blog post's summary paragraph and no further.
- Fluent until asked "why", then repeats the same sentence in different words.
- Cannot produce a case where the approach would be wrong.
- No numbers anywhere.
- Reaches for a second buzzword when pressed instead of a mechanism.

**The probe:** ask for the failure mode. Anyone who has actually run the thing knows how it breaks.
If the failure-mode answer is generic ("it could get slow"), the understanding is a summary and
should be scored as one.

**The second probe:** "when is this the wrong choice?" Genuine command includes the boundary.
Recited knowledge has no boundary because the source material had no boundary.

---

## 3. The retest protocol

A topic is not done because it was covered. It is done when a retest holds.

1. **Teach the specific defect**, not the whole topic again. Re-teaching everything is how prep time
   disappears; the defect was one link in the chain.
2. **Retest at the same level, with a different scenario.** Same scenario tests recall of your
   explanation, which is worthless.
3. **If it holds, retest one level up.** If that holds, mark `INTERVIEW READY` in the tracker.
4. **If it fails twice at the same level**, the problem is upstream. Drop a level and find the
   missing foundation — usually a distributed-systems or networking fundamental, not the topic
   itself.
5. **Retest cold in a later session.** Same-session retention is not retention. A topic that held on
   Tuesday and fails on Friday was never learned; log the delta and re-teach differently.

Write every attempt to `memory/knowledge-tracker.md` with level, score and the specific weak point.
**The delta between attempts is the evidence of learning; the first attempt alone tells you almost
nothing.**

---

## 4. Connecting to his experience — and when not to

Connecting a concept to something he has built makes it stick and gives him a story for the room.
But the connection has to be real.

- **Real bridge:** "You ran AMPS for real-time aggregation at 25M records/day — the backpressure
  problem there is the same shape as consumer lag here." That is a legitimate transferable claim and
  he can defend it.
- **Fake bridge:** "Your Kafka experience means you understand Flink." It does not, and the follow-up
  will find out.

If the bridge does not hold, say so and classify it as an **experience gap** (§5 of SKILL.md), which
is a positioning problem, not a study problem. Never manufacture a bridge to make a gap feel closed.

---

## 5. Teaching a genuine gap under time pressure

When a Tier 1 topic is new to him and the interview is close, do not attempt mastery. Build a
**defensible position**:

1. **One correct mental model** he can explain in ninety seconds.
2. **Two tradeoffs** he can name without prompting.
3. **One failure mode** he can describe concretely.
4. **The honest boundary** — the sentence that says what he has not done, without conceding
   competence: *"I haven't run this in production; here's how I'd approach it and what I'd want to
   verify first."*

That package survives most follow-ups. Attempting to sound experienced instead does not, and it
converts a manageable gap into a credibility problem.

---

## 6. Session shape

A good hour: **10 min recall of the last session (cold) · 25 min new material with questions
throughout · 15 min applied exercise · 10 min retest and tracker update.** Never spend an hour
explaining. If he has not answered a question in ten minutes, the session has become a lecture and
is producing nothing.

End every session with:

- What was tested, and the level it held at.
- The one thing to review before next time.
- What is next, and why it is next.

---

## Change log

| Date | Change |
|---|---|
| 2026-08-29 | File created with the skill. |
