# Sscout — the learning loop, in detail

SKILL.md §12 is the compact version. Read this before running `/sscout review`, resolving ledger
rows, or writing a lesson.

## Why three signals

| Signal | Measures | Fails at |
|---|---|---|
| Sai's feedback on a scan | Whether the output was *usable* — right roles, right depth, right filtering | Cannot tell you whether the fit score was correct. A well-presented wrong ranking reads well. |
| Application outcomes | Whether the score was *calibrated* — did employers agree | Slow, small sample, and silent on roles you never surfaced. |
| Missed roles / re-scan diffs | Whether *retrieval* was complete | Only fires when a miss happens to be discovered. |

Feedback tunes **how you scan**. Outcomes tune **what you score**. Misses tune **where you look**.
Keep them separate: a compliment is not calibration evidence, and one rejection is not a rubric
change.

## The feedback ask

**Ask when** the scan produced a real deliverable: a ranked company scan, a deep dive, a
compare, an apply/skip verdict on a pasted JD.

**Don't ask when**: he asked a definitional or logistics question; the exchange is mid-thread; you
already asked this conversation; or he is clearly moving fast.

**How**: one `AskUserQuestion`, one question, four options framed as *failure modes* rather than
satisfaction —

- **Useful as-is** — the ranking landed; nothing to change.
- **Missed roles I'd want** — the search was too narrow, or filtered out something relevant.
- **Too many marginal roles** — the bar was too low; noise cost him time.
- **Score disagrees with my read** — a specific role is ranked wrong.

Free-form "Other" text is higher signal than any option click. If the ask feels heavy, one closing
line does the job: *"Tell me if I missed anything or ranked something wrong — it goes in the file."*
Never ask twice in a turn, never pad with gratitude.

## Turning a reaction into a lesson

Write to `memory/lessons.md` only when the feedback implies a **repeatable behaviour change**.
Test: could you state it as an instruction that would change a future scan? If not, don't write it.

- "Too many marginal roles" once → provisional lesson about the reporting floor for this company
  type. Twice → `[confirmed]`, and state the new floor.
- "Missed roles I'd want" → this is a **retrieval defect**, not a style note. Run the miss
  post-mortem below.
- "Score disagrees with my read" → do not silently re-score. Ask which dimension he reads
  differently, then change the anchor in `references/scoring-rubric.md` and log it in that file's
  change log. A rubric edited without a written reason drifts back within a month.

Write the file in the same turn. A deferred lesson is a lost lesson.

## Miss post-mortem — the highest-value event

Sai finds a relevant role at a company you already scanned. Work out the mechanism, because the
mechanism generalizes and the individual role does not:

1. **Vocabulary** — an in-house title you never queried → add it to that company's lexicon in
   `memory/companies.md`, and if it is a general pattern (e.g. "Member of Technical Staff") add it
   to the equivalents list in `references/search-playbook.md`.
2. **Filter** — a location facet, a category facet, or a default search radius excluded it → note
   the ATS quirk in the playbook's ATS table.
3. **Source** — it lived on a subsidiary, executive, or acquired-brand board → record the extra
   URL in the dossier.
4. **Timing** — posted after your scan → not a defect. Note the company's posting cadence instead.
5. **Judgment** — you saw it and filtered it out → this is a *rubric* problem, not a search
   problem. Find the dimension you scored wrong.

Then write the lesson naming the mechanism, not the role.

## The application ledger

Log a row when Sai applies, or when he says a role is worth applying to and you want the score on
record. Record **the fit score you assigned at the time** — that is the whole point; a score
recorded after the outcome is worthless.

Statuses: `OPEN` → `SCREEN` (recruiter or hiring-manager contact) → `INTERVIEW` → `OFFER` |
`REJECTED` | `GHOSTED` (no response by check-by + 30 days) | `WITHDREW` | `VOID` (posting pulled,
req frozen).

`GHOSTED` is data, not a blank. A cluster of ghostings at one score band, one company type, or one
seniority level is a finding.

## `/sscout review`

Produce a scorecard, not a narrative.

1. **Tally** — applications by status; response rate overall; **response rate split by fit-score
   band**. The split is the headline: if 70-79 responds as well as 90-100, the scoring signal is
   not discriminating and that outranks everything else in the review.
2. **Resolve** every OPEN row past its check-by date.
3. **Pattern hunt** — where do the misses cluster? By company type (bank / big tech / consultancy /
   defense), by role type (IC vs architect vs director), by work style, by whether comp was
   published, by whether he had a referral.
4. **Retrieval audit** — for each company scanned more than once, how many roles appeared in the
   later scan that existed at the time of the earlier one? That number is your miss rate.
5. **Lesson maintenance** — promote provisional lessons with two supporting data points; retire
   lessons the record contradicts; merge duplicates.
6. **Rubric maintenance** — any anchor change goes in `references/scoring-rubric.md` with a dated
   change-log row.
7. **Report** — the tally, two or three patterns, what changed in the files, and the one behaviour
   you are changing next. Be blunt about a poor record; a scout that grades itself generously is
   worse than no scout.

Cadence: monthly, or whenever ~10 applications have accumulated. Can be run on a timer with
`/loop 30d /sscout review`.

## Housekeeping

- `memory/lessons.md`: keep under ~40 live lessons. Beyond that, merge — a bloated file stops being
  read, which is the only real failure mode of this system.
- `memory/companies.md`: keep the posting snapshot for each company's last two scans. Older
  snapshots go to `memory/companies-archive-YYYY.md`.
- `memory/applications.md`: archive to `memory/applications-archive-YYYY.md` past ~200 rows.
- `memory/candidate-profile.md`: update whenever Sai states a new constraint, preference, comp
  target or skill. Date every change — a stale profile silently corrupts every score you produce.
- All files are plain markdown, meant to be readable and editable by Sai directly.
