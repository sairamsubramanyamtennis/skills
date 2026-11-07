# House Log Protocol

The persistent record lives at **`C:\Users\ssair\house\`** — `HOUSE.md` (source of truth) and
`house-log.md` (chronological). SKILL.md §0 carries the read-before / write-after rule. This file
is the format and the judgement calls.

---

## 1. Log entry format

Newest entries at the top of `house-log.md`.

```markdown
## YYYY-MM-DD — <System>: <one-line symptom> <status emoji> <STATUS>

**System:** make/model, install date, installer, age at fault, indoor/outdoor.
**Symptom sequence (as reported):** what he actually said, in order, in his words.
**Diagnosis:** the fault, with the specific code or mechanism, and ranked causes.
**Key reasoning:** the non-obvious step — especially anything that rules OUT the obvious suspect.
**Root cause:** the underlying reason, distinct from the immediate fault. Note confidence.
**Prescribed, cheapest first:** numbered.
**Money at stake:** DIY cost · part cost · service cost · what a replacement pitch would cost.
**Warranty:** age vs typical term, and whether it was verified or still needs checking.
**Upsell guard:** what an unreasonable quote for this fault would look like.
**Outcome:** ⬜ pending — and exactly what is being waited on.
**Prevention:** what stops it recurring.
```

**Status key:** ⬜ open · ✅ resolved · ❌ tried and failed · ⏸️ deferred · 🔁 recurrence

Drop any line that would be padding. A log entry for "which caulk for the shower" needs three
lines, not twelve.

---

## 2. The outcome line is the whole point

Most of the value in this log is created **after** the answer, when Sai reports back.

- Open every entry with **⬜ pending** and state precisely what is being waited on — a photo, a
  model number, a vendor's answer, the result of a test.
- When he reports back, **edit the original entry.** Never open a second entry for the same
  incident; that breaks recurrence detection.
- Record **❌ tried and failed** as carefully as ✅. A ruled-out cause is worth as much as a
  confirmed one and stops the same dead end being walked twice.
- If the real cause turned out to be different from the diagnosis, **say so plainly in the entry**
  and note what the misleading signal was. That is the entry a future session learns most from.

---

## 3. Recurrence handling

Before diagnosing, scan the log for the same system.

If it has happened before, mark the new entry **🔁 recurrence of YYYY-MM-DD** and change the
approach:

- **A repeat failure means the root cause was never addressed.** The first-time diagnosis may
  have been right about the fault and wrong about the cause.
- Say what was done last time and **how long it held.** Six weeks and three years mean different
  things.
- Escalate the response: a fix that failed twice is a reason to replace the component or to fix
  the environment, not to clean it a third time.
- Check whether the prevention step from the earlier entry was ever actually done. Often it
  wasn't, and that is the answer.

---

## 4. What belongs in `HOUSE.md` versus the log

| Goes in `HOUSE.md` | Goes in `house-log.md` |
|---|---|
| Durable facts — model numbers, install dates, warranty terms, PEX vs copper, HOA rules | Individual incidents |
| The equipment register | The diagnosis of a specific fault |
| Standing conclusions that shouldn't be re-derived | The reasoning that produced one |
| Open items, as a short live list | The full detail behind each open item |
| Vendors | A specific service call |
| Facts still needed | — |

**Rule of thumb:** if it will still be true in five years, it goes in `HOUSE.md`. If it happened
on a date, it goes in the log.

---

## 5. Maintaining the equipment register

This is the highest-value table in either file, because **install date drives warranty and
warranty drives cost.**

Every time a system comes up, capture what you can: make, model, install date, installer,
warranty status, indoor/outdoor, and anything unusual about the installation.

- **Ask for the data plate photo** whenever a system appears for the first time. One photo now
  saves a diagnostic guess later. `references/diagnostic-playbook.md` §2 lists where the model
  number lives on each type of equipment.
- **Compute and record age at every mention**, not just at install. "4y 6m" is the number that
  triggers the warranty question.
- **Flag approaching warranty expiry proactively.** A system at 4y 6m against a likely 5-year term
  is worth mentioning even when he didn't ask, because after the term nothing can be done.
- Never invent an install date or a warranty term. **"Unknown — needs confirming"** is the correct
  entry, and it feeds the facts-still-needed list.

---

## 6. Keeping "facts still needed" honest

`HOUSE.md` §7 is the running list of what would sharpen future answers. Maintain it actively:

- **Add to it** whenever a question can't be answered fully for want of a fact.
- **Remove from it** the moment the fact arrives — a stale list gets ignored.
- **Keep it prioritised.** HVAC data plates and roof age outrank filter intervals, because they
  gate more future questions and more money.
- **Ask for at most one or two items per conversation**, and only when they're relevant to what he
  actually asked. A repair answer that ends in a homework list is annoying and will be skipped.

---

## 7. Privacy

These files are local and they describe his home.

Record what a repair needs — address for city/permit purposes, equipment, vendors, dates, costs.
**Do not copy personal contact details, account numbers, card numbers or financing details** out
of invoices into the log, even when they appear on the document. Vendor phone numbers are fine
and useful; his own are not needed for any repair question.
