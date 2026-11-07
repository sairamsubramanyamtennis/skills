# Sscout — scoring rubric

SKILL.md §4 carries the weights. This file carries the anchors, so that a 78 means the same thing
in March as it did in January. Score each dimension against these anchors, sum, then sanity-check
the band against the gut read — if the arithmetic says 84 and the role feels like a 65, one of the
dimension scores is wrong. Find it rather than overriding the total.

---

## 1. Seniority / scope — 25 points

The heaviest dimension because level, not technology, is what makes or breaks a senior move.

| Points | Anchor |
|---|---|
| 22-25 | Clearly at or above current level. Enterprise- or org-wide scope, sets technical direction others follow, Principal/Distinguished/Architect/Director+ equivalent. |
| 17-21 | At level. Owns architecture for a significant platform or a multi-team domain. |
| 11-16 | Slightly below or ambiguous. Senior-team-member scope, 8-12 years asked, influence limited to one team. |
| 5-10 | Down-level. Mid-senior IC work, execution-focused, "reports to a Lead". |
| 0-4 | Junior/mid, or a management-only role with no technical charter. |

Evidence beats title. Required years is the weakest of the signals (companies copy-paste it);
**scope words and reporting line are the strongest**.

## 2. Technical match — 25 points

| Points | Anchor |
|---|---|
| 22-25 | Core stack overlap — distributed systems / cloud-native on AWS / event-driven with Kafka / enterprise modernization, plus at least one of observability or applied GenAI. |
| 17-21 | Strong overlap with one meaningful stack difference (e.g. GCP or Azure instead of AWS, different streaming layer). Transferable within weeks. |
| 11-16 | Adjacent — same discipline, different substrate (e.g. embedded, game engines, heavy front-end, deep data-science modelling). |
| 5-10 | Mostly non-overlapping; he would be learning the core of the job. |
| 0-4 | Different discipline wearing a software title. |

Do **not** award points for keyword presence alone. A JD that lists Kafka once in a "nice to have"
block is not an event-driven architecture role.

## 3. Architecture / strategic influence — 15 points

| Points | Anchor |
|---|---|
| 13-15 | Explicitly owns architecture and standards; visible to and influencing senior leadership; shapes multi-year technical direction. |
| 9-12 | Significant architecture responsibility within a domain; sits on review boards or guilds. |
| 5-8 | Contributes to designs others own. |
| 0-4 | Execution role; architecture handed down. |

## 4. AI / cloud / modern-engineering relevance — 10 points

| Points | Anchor |
|---|---|
| 9-10 | Production GenAI/agentic systems, or a modern cloud platform charter — work that compounds his market value. |
| 6-8 | Cloud-native modernization; AI adjacent but real. |
| 3-5 | Some modern surface, mostly maintenance of established systems. |
| 0-2 | Legacy-only. Career-value risk — flag it. |

## 5. Compensation potential — 10 points

Score published bands where available; otherwise score the company's known band for the level and
**say the number is an estimate**.

| Points | Anchor |
|---|---|
| 9-10 | Published band clearly above his target; strong equity or bonus. |
| 6-8 | At target, or a wide band whose midpoint is at target. |
| 3-5 | Below target but plausibly negotiable, or undisclosed at a company that generally pays at market. |
| 0-2 | Published band clearly below target. Flag ⚠️. |

If comp is not disclosed and you have no reliable basis, award the midpoint (5) and say the
dimension is unresolved rather than guessing high.

## 6. Location / flexibility — 10 points

| Points | Anchor |
|---|---|
| 9-10 | Remote US, or DFW-based with real flexibility. |
| 6-8 | Hybrid within DFW commuting range, 2-3 days on site. |
| 3-5 | Hybrid elsewhere with meaningful travel-instead-of-relocation, or DFW onsite 5 days. |
| 0-2 | Onsite outside DFW / relocation required. Flag ⚠️. |

## 7. Career upside — 5 points

Where the role leads: promotion path to Distinguished/Fellow or executive technology leadership,
brand value, exposure to a domain that is growing, network quality, optionality if the company is
acquired or the market turns.

| Points | Anchor |
|---|---|
| 5 | Clear ladder to Distinguished/Fellow/VP, or a marquee brand in a growing domain. |
| 3-4 | Solid, lateral-plus. |
| 1-2 | Terminal role — good work, limited next step. |
| 0 | Career-value negative (shrinking business, legacy-only charter). |

---

## Calibration rules

- **Score the role as posted, not as you hope it is.** If a JD is vague, score the vagueness — and
  say which dimension the ambiguity sits in.
- **Never round up to reach a band.** A 79 stays a 79. The bands mean things: 80+ means "worth the
  application effort", and inflating into it wastes his cycles.
- **The 60 floor is a filter, not a wall.** A sub-60 role can still appear in "considered but
  rejected" with a one-line reason — that section is what proves coverage.
- **Recheck against outcomes.** `memory/applications.md` records the score you gave and what
  actually happened. If 90s and 70s produce the same response rate, an anchor above is wrong; find
  it during `/sscout review` and change it here, in this file, with a dated note.

---

## Change log

Amend the anchors above only from evidence, and record it here.

| Date | Change | Evidence |
|---|---|---|
| 2026-08-22 | Initial rubric. | Persona specification. |
