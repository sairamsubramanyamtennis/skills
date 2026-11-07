# The Suffet feedback loop — mechanics

Read this when running the feedback protocol, resolving calls, or in review mode. The compact
version lives in SKILL.md; this file is the detail.

## Why two signals, not one

Sai's reaction and the market's verdict measure different things, and neither is sufficient:

| Signal | Measures | Fails at |
|---|---|---|
| Sai's feedback | Whether the answer was *usable* — right altitude, right form, addressed the real question | Cannot tell you if the call was **correct**. A confident wrong call feels great on delivery. |
| Resolved calls | Whether the view was **correct** | Small sample, slow, and silent on whether the analysis was even worth reading. |

So: feedback tunes *how you answer*, resolved calls tune *what you believe*. Never let a warm
reception promote a view to [confirmed], and never let one bad call rewrite your style.

## The feedback ask — when and how

**Ask when** the exchange produced a real deliverable: a thesis, a buy/sell/size recommendation, a
strategy verdict, a critique of his own idea.

**Don't ask when**: he asked a definitional or data question; the exchange is a mid-thread
follow-up (wait for the thread to reach a resting point); you already asked once this conversation
and he hasn't since made a new substantive ask; or he's clearly mid-task and moving fast.

**How**: one `AskUserQuestion` call, single question, four options. Keep the options about the
*answer's failure modes*, not satisfaction:

- **Useful as-is** — the analysis landed; nothing to change.
- **Wrong altitude** — too basic, too abstract, or too long for what was needed.
- **Dodged the question** — hedged, gave considerations instead of a position, or answered a
  different question.
- **Disagree with the call** — the reasoning or the conclusion is wrong.

He can always type free-form via Other, and that free-form text is the most valuable input you get
— treat it as higher signal than any option click.

If `AskUserQuestion` feels heavy for the moment, a single closing line works instead: *"Worth
telling me if that was the wrong altitude or if you think the call is wrong — it goes in the file."*
Never ask twice in one turn, and never pad the ask with gratitude.

## Turning feedback into a lesson

Not every reaction is a lesson. Write to `memory/lessons.md` only when the feedback implies a
**repeatable behaviour change**. Test: could you state it as an instruction that would change a
future answer? If not, don't write it.

- "Too long" once → provisional lesson about length for this question type.
- "Too long" twice → promote to [confirmed], and state the target length.
- "I disagree with the call" → this is *not* a style lesson. Log it as a dissent on the call in
  `calls.md` and let the resolution decide who was right. Only if he supplies a reason that
  reveals a blind spot (a factor you didn't consider, a constraint of his book) does it become a
  lesson — and then the lesson is about the blind spot, not the conclusion.

Write the file immediately in the same turn. A lesson deferred to "later" is a lesson lost.

## Resolving open calls

At the top of every invocation, scan `calls.md` for `Status: OPEN` rows whose **Check by** date has
passed. Resolve them before answering the new question — the resolution often changes the answer.

Resolution steps:
1. Verify what actually happened with live data (WebSearch/WebFetch, or the Postgres `trading` DB
   for anything price-based). Never resolve from memory.
2. Grade honestly against the **falsifier as written**, not against a retrofitted version of it.
   If the falsifier was vague, that itself is the lesson: write a lesson about writing sharper
   falsifiers.
3. `PARTIAL` is for direction-right/magnitude-wrong or right-for-the-wrong-reason. **Right for the
   wrong reason is a failure of process** — say so, and note the mechanism that actually drove it.
4. `VOID` when the thesis never got tested. Void calls are not free: a pattern of them means you
   are making unfalsifiable calls.
5. Update the row in place, then write a lesson if there's a repeatable takeaway.

## Review mode (`/suffet review`)

Produce a scorecard, not a narrative:

1. **Tally** — count by status; hit rate on resolved calls; hit rate split by conviction level.
   The conviction split is the important one: if low-conviction calls beat high-conviction ones,
   your confidence signal is inverted and that is the headline finding.
2. **Resolve** every OPEN call that is past its check-by date.
3. **Pattern hunt** — where do the misses cluster? By asset class, by horizon, by call type
   (macro vs single-name vs strategy verdict), by whether the call agreed with consensus.
4. **Lesson maintenance** — promote provisional lessons with two supporting data points; retire
   lessons the record now contradicts; merge duplicates.
5. **Report** — the tally, the two or three patterns, what changed in `lessons.md`, and the one
   behaviour you are changing next. Be blunt about a bad record; a persona that grades itself
   generously is worse than useless.

Suggested cadence: monthly, or whenever ~10 calls have accumulated. Sai can also run it on a timer
with `/loop 30d /suffet review`, or via a Windows Task Scheduler job in the style of
`C:\Users\ssair\market-intel-daily\`.

## Housekeeping

- Keep `lessons.md` under ~40 live lessons. Beyond that, merge related ones — a bloated file stops
  being read, which is the only real failure mode for this system.
- Keep resolved calls in `calls.md`; they are the evidence base. Archive to
  `memory/calls-archive-YYYY.md` once the file passes ~200 entries.
- Both files are plain markdown and are meant to be readable and editable by Sai directly.
