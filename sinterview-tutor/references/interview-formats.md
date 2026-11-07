# Interview formats and interviewer personas

SKILL.md §11 is the compact version. Read this before running a mock or predicting questions.

The single most common preparation error at senior level is **preparing for one interview and
walking into five different ones.** A Principal Engineer, a VP and a product leader ask about the
same platform and want completely different answers. Getting the audience wrong loses rounds that
knowledge alone would have won.

---

## 1. Round types

| Round | Who runs it | What it actually tests | Failure mode |
|---|---|---|---|
| **Recruiter screen** | Recruiter | Level, comp, logistics, whether the resume story is coherent | Rambling; no crisp 90-second narrative |
| **Technical screen** | Senior/Staff engineer | Whether the resume is real | Vocabulary without mechanism |
| **Architecture round** | Principal / Enterprise Architect | Judgment and defence of past decisions | Describing systems instead of defending choices |
| **System design** | Principal / Staff | Designing under constraint | See `system-design-rubric.md` |
| **Cloud / platform deep dive** | Platform lead | Operational reality | Service names without operational detail |
| **AI/GenAI architecture** | AI lead | Whether he has shipped or only read | Conflating process-AI with production AI systems |
| **Coding concepts** | Engineer | Whether he still thinks like a builder | Delegating the answer ("my team would...") |
| **Leadership / influence** | Director / VP | Impact without authority | Stories with no conflict and no cost |
| **Behavioral** | Anyone, often HR | Ownership, failure, conflict, values | "We" throughout; no failure story |
| **Hiring manager** | The future boss | Fit for *this* problem and this team | Generic answers; no view on their actual problem |
| **Executive** | CTO / senior exec | Strategy, judgment, presence | Descending into implementation detail |
| **Panel / loop debrief** | Several at once | Consistency and composure | Different story to different people |

**Ask which round this is before every mock.** A mock at the wrong altitude is worse than no mock:
it rehearses the wrong instinct.

---

## 2. Personas — what each one is listening for

### Senior / Staff Engineer
Listening for: has he actually built this. Probes implementation detail, edge cases, debugging.
Wins with: specific mechanisms, war stories, honest boundaries.
Loses with: management vocabulary, delegated answers, hand-waving over the hard part.

### Principal / Distinguished Engineer
Listening for: judgment, taste, and whether he knows the boundary of his own approach.
Probes: alternatives rejected, failure modes, scale, cost, "when is this wrong."
Wins with: committing to a position and defending it, then updating on a genuinely better argument.
Loses with: balanced surveys with no recommendation, and stubbornness that survives a good counter.

### Enterprise Architect
Listening for: how he works across organizations he does not control.
Probes: standards, governance, target state, integration, how decisions get made and enforced.
Wins with: concrete mechanisms — a review board, a paved road, a deprecation plan with dates.
Loses with: purely local optimization, or governance described as a document rather than a behaviour.

### Engineering Manager
Listening for: is he easy to work with, and does he deliver.
Probes: collaboration, disagreement, delivery under pressure, mentoring.
Wins with: specific people-shaped stories where he changed his own position.
Loses with: hero narratives in which everyone else was the problem.

### Director / VP Engineering
Listening for: leverage. What changes across the org because he is here.
Probes: influence without authority, prioritization, risk, technology strategy, business impact.
Wins with: outcomes in business terms, with a number and a timeframe.
Loses with: depth for its own sake. **A VP asking about Kafka wants to know why it was worth the
money.**

### CTO / Executive
Listening for: judgment at portfolio scale, and presence.
Probes: what he would change in the first ninety days, where the industry is going, build vs buy,
what he would kill.
Wins with: a clear point of view, held lightly, with the reasoning visible.
Loses with: implementation detail, and with agreeing with everything.

### Product leader
Listening for: can engineering be explained to non-engineers without either condescension or fog.
Probes: tradeoff communication, timelines, why something is hard.
Wins with: analogies that are accurate, and honesty about cost.
Loses with: jargon, and with "it depends" as a final answer.

---

## 3. Behavioral competencies at senior level

The generic list is not what senior loops probe. These are:

| Competency | The question underneath |
|---|---|
| Influence without authority | Can he move an org he does not own? |
| Technical disagreement | Can he lose an argument well, and win one without damage? |
| Failure and recovery | Will he tell the truth about something that went wrong? |
| Ambiguity | Can he act before the requirements are clear? |
| Prioritization and saying no | Does he protect the important thing from the urgent one? |
| Mentoring and multiplying | Does the team get better because he is there? |
| Stakeholder and executive communication | Can he brief someone senior in three minutes? |
| Ownership | Does "we" become "I" when asked what *he* did? |
| Change leadership | Has he moved people, not just systems? |

**The failure question is the one most often failed.** Deflected failure stories ("the vendor let us
down") read as a candidate who will not own an outage. A usable failure story has: a real cost, his
own decision as a cause, what he did about it, and what he does differently now. If he does not have
one on file, that is a Tier 1 prep item regardless of the JD.

---

## 4. Running a full loop simulation

Rounds back to back, in the real order, with short breaks. Change persona between rounds and say who
you are now. Do not debrief between rounds — a real loop gives no feedback, and composure across
rounds is part of what is being measured.

At the end: per-round scorecard, composite readiness, hiring signal, and **consistency check** — did
he tell the same story about the same project to three different people? Inconsistency across a
panel is a common and quiet rejection reason that a single-round mock cannot detect.

---

## Change log

| Date | Change |
|---|---|
| 2026-08-29 | File created with the skill. |
