# The learning loop, in detail

SKILL.md §16 is the compact version. Read this before running `/sinterview-tutor review`, running a
`DEBRIEF`, or writing a lesson.

---

## Why three signals

| Signal | Measures | Blind to |
|---|---|---|
| Sai's reaction to a session | Whether the coaching was *usable* — right topics, right pressure, right depth | Whether the prediction was right. A pleasant session can prepare him for the wrong interview. |
| Tracker deltas across sessions | Whether he is actually *learning* — retest performance over time | Whether what he learned was what would be asked. |
| Real interview outcomes | Whether the predictions and readiness scores were *calibrated* | Slow, small-sample, and silent about the rounds he never reached. |

Feedback tunes **how you coach**. Deltas tune **what you teach next**. Outcomes tune **what you
predict and how confidently you score**. Never let a warm session promote a coaching habit, and never
let one rejection rewrite a rubric.

---

## The feedback ask

**Ask when** the session produced a real deliverable: a full mock, a system-design round, a gap
analysis, a plan, a red team.

**Don't ask** mid-mock, after a definitional question, twice in a conversation, or when he is
clearly moving fast.

**How:** one `AskUserQuestion`, four options framed as failure modes —

- **Right pressure, useful** — the session landed.
- **Too easy** — an interviewer would have pushed harder than you did.
- **Wrong topics for this job** — a prediction/mapping defect, not a teaching one.
- **Too much teaching, not enough practice** — the ratio was wrong.

Free-form "Other" is worth more than any option click. If a formal ask feels heavy, one closing line
works: *"Tell me if that was the wrong pressure or the wrong topics — it goes in the file."*

---

## Turning a reaction into a lesson

Write to `memory/lessons.md` only when the reaction implies a **repeatable behaviour change**. Test:
could you state it as an instruction that would change a future engagement? If not, do not write it.

| Reaction | What it is evidence of | Fix |
|---|---|---|
| "Too easy" | Your Level 4/5 questions are Level 3 questions | Harden the question bank; require a number, an asymmetry and a consequence (`tutor-method.md` §1) |
| "Wrong topics" | Competency-map or probability defect | Re-weight; find the JD signal you misread; update `competency-map.md` |
| "Too much teaching" | Ratio defect | Shift the session shape toward practice; teaching is the default failure of a tutor persona |
| "Right pressure, useful" | Baseline confirmed | **Write nothing.** Keeping the format is not a behaviour change |

Grade `[confirmed]` · `[provisional]` · `[retired]`. Write in the same turn.

---

## The debrief — mechanics

Run `DEBRIEF` within 24 hours of a real interview; recall decays fast and the question list is the
asset.

Capture in `memory/outcomes.md`:

1. **Questions asked**, verbatim where he can manage it, grouped by round.
2. **Prediction grading** — for each question you forecast, mark `HIT` / `MISS`. For each question
   asked that you never forecast, mark `UNPREDICTED` and diagnose the mechanism.
3. **Performance** — where he stumbled, and whether prep had covered it:
   - **Prepped and stumbled** → *teaching* defect. The topic was taught but did not hold. Was it
     retested? Cold-retested? Was it taught at Level 4 or only Level 2?
   - **Not prepped** → *prediction* defect. Fix the map, not the teaching.
   - These have different fixes and merging them is how a coach stops improving.
4. **Outcome**, when it arrives, against the readiness score you gave and the date you gave it.

### Unpredicted-question post-mortem

Each unpredicted question is a defect with a mechanism. Find it:

| Mechanism | Fix |
|---|---|
| A JD line you weighted too low | Adjust the probability signals in `competency-map.md` |
| A competency category you did not map | Add it |
| Company practice you did not research | Add the research step for this company type |
| A round type you did not model | Add it to `interview-formats.md` |
| Wrong interviewer persona | Update the engagement's panel model and the persona table |
| Genuinely idiosyncratic | Not a defect. Record it; do not over-fit one interviewer's hobby-horse |

The mechanism generalizes; the individual question does not. Write the lesson about the mechanism.

---

## `/sinterview-tutor review`

A scorecard, not a narrative.

1. **Prediction hit rate.**
   - *Precision* — of questions forecast Very High/High, what fraction was asked?
   - *Recall* — of questions actually asked, what fraction was forecast at all?
   - Report both. High precision with low recall means the map is too narrow; the reverse means it
     is padded and the ranking is not doing work.
2. **Readiness calibration.** Group past engagements by the readiness score at interview time and
   compare against outcomes. If 85s and 65s advance at the same rate, **say so plainly** — the score
   is noise and that finding outranks everything else in the review.
3. **Teaching effectiveness.** Of topics taught and then tested in a real interview, what fraction
   held? Split by whether they were cold-retested during prep — that split usually tells you the
   whole story about the retest protocol.
4. **Pattern hunt.** Where do failures cluster — round type, persona, competency category, company
   type, time-budget template, or the gap between prep end and interview date?
5. **Lesson maintenance.** Promote provisionals with two supporting data points; retire what the
   record contradicts; merge near-duplicates.
6. **Structural self-edit.** When a `[confirmed]` lesson implies a change to this skill's own files,
   make the edit and log it in that file's change log with the date and the reason. This is the
   outer recursion. An undocumented rubric change drifts back within a month, so the log entry is
   not optional bookkeeping — it is the mechanism.
7. **Report.** The two hit-rate numbers, the calibration verdict, two or three patterns, what changed
   in the files, and the one behaviour changing next.

Cadence: after every real interview, and whenever ~5 sessions have accumulated. Can be scheduled with
`/loop 30d /sinterview-tutor review`.

---

## Housekeeping

- `memory/lessons.md` — keep under ~30 live lessons. Beyond that, merge. A bloated lessons file stops
  being read, which is the only real failure mode of this system.
- `memory/knowledge-tracker.md` — keep every competency row; keep only the last three attempts per
  competency plus the first (the first is the baseline that makes the delta meaningful).
- `memory/story-bank.md` — no limit. This is the compounding asset. Retire a story only when it has
  landed flat twice, and say why in the row.
- `memory/engagements.md` — archive closed engagements past ~20 rows to
  `memory/engagements-archive-YYYY.md`.
- `memory/outcomes.md` — never archive. It is the calibration record and it is small.
- All files are plain markdown, meant to be read and edited by Sai directly.

---

## Change log

| Date | Change |
|---|---|
| 2026-08-29 | File created with the skill. |
