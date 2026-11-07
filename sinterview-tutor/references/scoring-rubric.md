# Scoring rubric — answers, and the readiness score

SKILL.md §12 is the compact version. Read this before scoring a mock answer or quoting a readiness
number.

**The governing rule: score what he actually said, not what he probably knows.** An interviewer has
no access to his unstated knowledge either. Generous scoring is the failure mode of every coach; it
produces confidence that cannot survive the room.

---

## 1. The ten answer dimensions

Score 1-5. Not every dimension applies to every question — score only what the answer had a chance
to demonstrate, and say which you skipped.

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| **Technical correctness** | Wrong in a way that matters | Correct with a gap or imprecision | Correct, precise, including the edge case |
| **Depth** | Vocabulary only | Explains how it works | Explains why it works that way and what it costs |
| **Architecture thinking** | Describes components | Describes components and flow | Reasons about the system's properties, not its parts |
| **Tradeoff awareness** | Presents one option as obvious | Names alternatives | Names alternatives, the constraint that decides, and what he gives up |
| **Communication** | Rambling, or so terse the interviewer must dig | Clear, follows the answer | Structured, signposted, easy to interrupt and resume |
| **Structure** | No shape | Recognizable beginning and end | Frames the answer up front, delivers it, lands it |
| **Confidence** | Hedged into meaninglessness, or bluffing | Steady | Commits to a position and holds it without rigidity |
| **Relevance** | Answers a different question | Answers the question | Answers the question *and* the reason it was asked |
| **Evidence from experience** | Abstract throughout | Mentions a real project | Grounds the answer in a specific system, with a number |
| **Senior-level judgment** | Reasons like an implementer | Reasons like a lead | Reasons about risk, cost, org and time horizon |

### The four failure signatures worth naming explicitly

- **Correct but shallow** — 5 on correctness, 2 on depth. Passes the question, fails the follow-up.
  The most common senior-loop failure and the hardest for a candidate to self-detect.
- **Buzzword density** — 4 on communication, 2 on depth. Sounds excellent, contains no mechanism.
- **Implementer's altitude** — a Principal candidate answering at Senior level. Correct, detailed,
  and reads as one level down. Costs the level, not the offer.
- **The unowned story** — "we" throughout. The interviewer cannot tell what he did, and defaults to
  assuming the answer is "less than it sounds."

---

## 2. The feedback block

Fixed order. Never reorder to soften.

1. **What was strong** — specific, not "good answer." If nothing was strong, say so in one line.
2. **What was missing** — the specific content, not "more depth."
3. **What would hurt in the real room** — the sentence an interviewer would seize on, quoted back.
4. **The better reasoning path** — how he should have thought about it, not the answer to recite.
5. **An improved answer** — in his voice, using only his facts. Never insert an accomplishment,
   metric, or claim he did not supply.
6. **The follow-up** — what the interviewer asks next, given what he just said. Then ask it.

Step 6 is what makes this a loop instead of a review.

---

## 3. Readiness score, 0-100

| Component | Weight | Scored from |
|---|--:|---|
| Technical knowledge | 25 | Quiz + tutor answers across Tier 1-2 competencies |
| System design | 20 | Completed design rounds, dimension coverage and attack survival |
| Architecture judgment | 15 | Tradeoff and failure-mode reasoning across all rounds |
| Relevant experience stories | 15 | Story-bank coverage of the slots this role will probe, with numbers |
| Communication | 10 | Structure and clarity across mock answers |
| Behavioral / leadership | 10 | Behavioral mock performance |
| Company / role understanding | 5 | Can he say what this team is trying to do and why they are hiring |

### Component anchors

Score each component 0-100, then weight.

| Band | Meaning |
|---|---|
| **90-100** | Would impress a skeptical interviewer at this level. Holds under adversarial follow-up. |
| **80-89** | Solid hire signal. Holds under normal follow-up; a hard push finds an edge. |
| **70-79** | Passes on a good day. One unlucky question exposes it. |
| **60-69** | Visible weakness. An attentive interviewer will find it. |
| **below 60** | Would fail if this area is tested. |

### The untested-competency rule

**Never score a competency he has not been tested on.** Report it as `UNTESTED` and exclude its
weight from the composite, renormalizing the rest — then state the coverage explicitly:

> `READINESS: 78/100 — from 62% of the weighted map. System design and behavioral untested.`

A readiness score from 30% coverage is not a readiness score. Say so rather than dressing it up.

### Fatal gaps

A fatal gap overrides the composite and is stated **above** it, never in a footnote. A gap is fatal
when it is (a) a Critical competency in the map, (b) Very High probability, and (c) currently below
60. One fatal gap makes any composite misleading.

```
READINESS: 78/100  (from 62% of the weighted map)

⚠ FATAL GAP — cannot explain multi-region failover. The JD names multi-region
  resilience in responsibility #2. This will be asked. Fix before anything else.

Strong:      Kafka and event-driven · data mesh · AWS core · stakeholder influence
Needs work:  Kubernetes internals · consistency models
Untested:    System design (0 rounds) · behavioral (0 rounds)

Smallest set of improvements likely to change the outcome:
  1. One session on multi-region failover + a retest at Level 4.
  2. One full system-design round on the deposits problem.
  3. Two behavioral stories with real numbers for the conflict and failure slots.
```

The last block is the deliverable. A score without it is a grade, not coaching.

---

## 4. Hiring signal (end of a full loop simulation)

**STRONG HIRE · HIRE · LEAN HIRE · LEAN NO HIRE · NO HIRE.**

Give the signal an interviewer would actually give — including the ones he will not enjoy. Then name
the *smallest* set of changes that would move it up one band. Bands move on a few specific defects,
not on general improvement.

---

## Change log

| Date | Change |
|---|---|
| 2026-08-29 | File created with the skill. |
