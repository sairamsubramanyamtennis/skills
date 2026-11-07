# Story bank — mining real experience into interview evidence

SKILL.md §10 is the compact version. Read this before eliciting or structuring stories.

**The absolute rule: never invent an accomplishment, a metric, a role or an outcome.** If the
information is not in the resume he supplied or in something he says in session, ask. An invented
detail becomes a sentence he says in a real interview to a person who can check it.

---

## 1. The slots

Fill these; leave the rest empty and visible.

| Slot | Why a senior loop wants it |
|---|---|
| Major architecture decision | The core of every architecture round |
| Large production incident | Tests ownership and operational reality |
| Scalability challenge | Tests whether scale is lived or read |
| Migration | Modernization roles hire for exactly this |
| Modernization / legacy | Same, at org scale |
| Performance improvement | Tests measurement discipline |
| Cloud implementation | Tests whether cloud was used or merely bought |
| Data architecture | Increasingly the differentiator |
| Technical disagreement | The most-asked leadership question at Principal+ |
| Influencing senior stakeholders | The Director/VP round lives here |
| Mentoring / growing engineers | Multiplier evidence |
| A failure | The question most often failed. Non-negotiable |
| A hard tradeoff | Judgment evidence |
| Security problem | Regulated-industry loops always probe this |
| Reliability improvement | SRE-adjacent roles |
| Cost optimization | Executive rounds |
| AI / GenAI implementation | Currently the highest-leverage slot |

An empty slot is a **risk register entry**, not a hole to fill with something plausible. Record it as
`EMPTY — no story on file` and decide with him whether to hunt for one or plan the honest answer.

---

## 2. Elicitation — questions that actually surface a story

Generic prompts ("tell me about a challenge") return generic answers. These work:

- "What is the hardest technical decision you made in the last three years — one where you could
  have reasonably gone the other way?"
- "What broke in production that you still think about?"
- "What did you build that is still running, and what surprised you about how it aged?"
- "When did you tell a senior person something they did not want to hear? What happened next?"
- "What did you argue for and lose? What did you do afterwards?"
- "What did you kill, deprecate, or refuse to build?"
- "What was the number before you started, and after?"
- "What is the largest thing you have owned — by users, transactions, dollars, or people?"
- "Where did you change your mind after seeing the data?"
- "What did the last real outage cost, and what did you change so it could not repeat?"

Follow every answer with the two questions that make it usable: **"What did *you* personally do?"**
and **"What was the number?"**

---

## 3. Structure

**Technical story — Context → Decision → Why → Tradeoff → Result.** The Tradeoff element is what
makes it senior; a story with no cost named reads as marketing.

**Behavioral story — Situation → Challenge → Action → Result → Learning.** The Learning element is
what makes it credible at Principal+; the interviewer wants evidence of a person who updates.

**Length: 60-90 seconds spoken.** Longer and the interviewer stops listening and starts waiting.
Structure them so they can be *interrupted and resumed* — senior interviewers interrupt.

Every story carries a **one-line headline** he can lead with, so the interviewer knows where the
story is going before it starts.

---

## 4. The two disciplines

### Ownership
"We" is correct for context and fatal in the Action. If the Action is genuinely collective, the story
is weaker than it appears — say so, and either find his specific contribution or move the story to a
lower slot. The interviewer's silent question throughout is *what did this person do*, and an
unanswered version of it defaults to "less than it sounded."

### Numbers
Every story needs one real figure and its denominator. "Improved performance by 40%" is worth
nothing without "from 2.1s p99 to 1.3s, measured over the following quarter across all deposit
inquiries." Mark `[needs metric]` where he has not supplied one and **ask before the next session** —
never fill it in yourself, and never let an unmetered story into a rapid-review sheet without the
marker.

---

## 5. Mapping stories to the job

For each engagement, map slots to competencies from the map: which story answers which likely
question. A story that answers a Very High probability question gets rehearsed; a story with no
likely question does not, however good it is.

Watch for **overuse**: the same project answering six questions makes a career look narrow. If one
project dominates the bank, deliberately mine an older role for two or three stories — depth of
career is itself a signal at senior level.

---

## 6. File format

Write confirmed stories to `memory/story-bank.md`:

```
## S00N — <headline> — <slot(s)>
**Employer / period:** <where and when>
**Context:** <2-3 lines>
**Challenge:** <the actual difficulty, not the task>
**Action (his):** <what HE did — first person, verified>
**Result:** <outcome + the number + the denominator>  [needs metric]
**Learning:** <what he does differently now>
**Answers:** <the question types this story serves>
**Confidence:** [confirmed by Sai YYYY-MM-DD] | [from resume] | [needs confirmation]
**Used in:** <engagements where it was rehearsed or told, and how it landed>
```

`Used in` is what makes the bank compound: after a real interview, record which stories were told
and how they landed. A story that lands twice is a keeper; one that draws a flat follow-up twice
needs rebuilding or retiring.

---

## Change log

| Date | Change |
|---|---|
| 2026-08-29 | File created with the skill. |
