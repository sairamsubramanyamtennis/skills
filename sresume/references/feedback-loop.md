# Sresume — the learning loop, in detail

SKILL.md §15 is the compact version. Read this before running `/sresume review`, before writing a
lesson, or before deciding whether a reaction is worth recording.

## Why three signals

| Signal | Measures | Blind to |
|---|---|---|
| The user's reaction to a draft | Whether the *writing* was right — voice, level, emphasis, length | Whether the positioning works. A draft he likes can still get no interviews. |
| What happened after applying | Whether the *positioning* was effective — did employers respond | Slow, small-sample, and silent about the versions he never sent. |
| New facts learned while working | Whether the *factual base* is complete | Only fires when a gap happens to surface in conversation. |

**Reactions tune how you write. Outcomes tune how you position. New facts tune what you have to
work with.** Keep them separate. A compliment is not calibration evidence, and one rejection is not
a reason to rewrite a positioning strategy.

## The feedback ask

**Ask when** the turn produced a real deliverable: a full audit, a rewritten resume, a targeted
variant, a built document, a humanization pass.

**Don't ask when**: he asked a definitional question; the exchange is mid-draft; you already asked
this conversation; or he is clearly moving fast.

**How**: one `AskUserQuestion`, one question, four options framed as *failure modes* rather than
satisfaction —

- **Ready to send** — it landed; nothing to change.
- **Doesn't sound like me** — voice defect. The highest-value answer in this file.
- **Wrong emphasis for this role** — positioning or selection is off, not the prose.
- **Overstates / understates something** — an accuracy or calibration problem on a specific claim.

Free-form "Other" text is higher signal than any option click. If a formal ask feels heavy, one
closing line does the job: *"Tell me if anything doesn't sound like you — it goes in the file."*
Never ask twice in a turn, never pad with gratitude.

## Turning a reaction into a lesson

Write to `memory/lessons.md` only when the reaction implies a **repeatable behaviour change**.
Test: could you state it as an instruction that would change a future draft? If not, don't write it.

- **"Doesn't sound like me"** → voice defect, never a style preference. Run the post-mortem below,
  fix `memory/style-profile.md`, then write the lesson.
- **"Wrong emphasis"** → a positioning or selection error. Ask which part he would have led with;
  the answer usually reveals how he sees his own identity, which belongs in the style profile *and*
  in the candidate model.
- **"Overstates something"** once → provisional lesson about a claim class (scale, leadership
  scope, AI production-vs-experimental). Twice → `[confirmed]`, and state the new default. A
  pattern of overstatement is the most dangerous failure this skill has: it survives the resume and
  detonates in the interview.
- **"Understates something"** → usually means a skill was graded *possible* when it was
  *strongly evidenced*. Fix the grading, not the sentence.

Write the file in the same turn. A deferred lesson is a lost lesson.

## The voice post-mortem — the highest-value event

He says a draft doesn't sound like him. Find the **mechanism**, because the mechanism generalizes
and the sentence does not:

1. **Vocabulary** — a word he would never use. Add it to the avoid-list in `style-profile.md`, and
   record the word he uses instead.
2. **Register** — too formal, too promotional, or too casual for him. Note where his register
   actually sits, with an example of his own writing.
3. **Inflation** — a claim pitched above what he would say aloud. This is the dangerous one:
   record the claim class, not just the claim.
4. **Detail level** — he volunteers more (or less) technical specificity than the draft did.
5. **Uniformity** — the structure was too even. A §6 pass failure; note which structure repeated.
6. **Identity** — the draft framed him as something he doesn't consider himself. This is a
   *positioning* miss wearing a voice costume; fix the candidate model too.

Then write the lesson naming the mechanism.

## The version ledger

Log a row in `memory/versions.md` whenever you produce a variant he might actually send. Record
**the positioning statement it used** — that is the whole point; positioning noted after the
outcome is worthless.

Statuses: `DRAFT` → `SENT` → `SCREEN` → `INTERVIEW` → `OFFER` | `REJECTED` | `GHOSTED` (no response
in 30 days) | `WITHDREW`.

`GHOSTED` is data, not a blank. A cluster of ghostings on one positioning, one level, or one
variant is a finding.

Cross-reference `sscout`'s `memory/applications.md` — it holds the fit score assigned at
application time. Fit score × resume version × outcome is a far better calibration signal than
either file alone: a high-fit role that went nowhere with the architect framing is evidence about
the *resume*, not about the role.

## `/sresume review`

Produce a scorecard, not a narrative.

1. **Tally** — versions by status; response rate overall; **response rate split by positioning**.
   That split is the headline. If the executive framing and the architect framing respond the same,
   positioning is not the lever and you should say so.
2. **Resolve** every `SENT` row older than 30 days.
3. **Pattern hunt** — where do responses cluster? By level targeted, by company type, by variant,
   by whether the JD was analyzed first, by whether he had a referral (referrals swamp resume
   effects — segment them out or the analysis is worthless).
4. **Factual drift audit** — diff the JSON sources of every live variant against
   `master-career-resume.md`. Any date, title, metric or scope claim that disagrees is a defect;
   fix it in every variant, not just the one you noticed.
5. **Lesson maintenance** — promote provisional lessons with two supporting data points; retire
   lessons the record contradicts; merge duplicates.
6. **Style profile maintenance** — is it still describing how he writes? Voice drifts as a career
   moves.
7. **Report** — the tally, two or three patterns, what changed in the files, and the one behaviour
   you are changing next. Be blunt about a poor record. A resume writer that grades itself
   generously is worse than none.

Cadence: after roughly ten applications, or quarterly. Can run on a timer with
`/loop 30d /sresume review`.

## Housekeeping

- `memory/lessons.md` — keep under ~40 live lessons. Beyond that, merge; a bloated file stops being
  read, which is the only real failure mode of this system.
- `memory/master-career-resume.md` — the factual spine. Every new project, metric, title or
  certification goes here **first**, then into variants. Date every addition.
- `memory/style-profile.md` — update on every voice signal. Quote his actual words; paraphrase
  loses the thing being recorded.
- `memory/versions.md` — archive to `versions-archive-YYYY.md` past ~100 rows.
- All files are plain markdown, meant to be read and edited by Sai directly.
