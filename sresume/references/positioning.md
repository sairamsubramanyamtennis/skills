# Positioning, seniority and job targeting

SKILL.md §3 and §4 are the compact versions.

## The seniority ladder, and the vocabulary that signals each rung

Level is communicated by **scope of consequence**, not by adjectives. Each rung below lists what
the resume must show and the language that reads native at that level.

| Level | Show | Native language |
|---|---|---|
| **Early career** | Coding, implementation, projects, testing, learning velocity, individual contribution | built, implemented, wrote, tested, contributed to, learned |
| **Mid / Senior Engineer** | Independent ownership of components, design decisions, reliability, performance, problem solving, mentoring | owned, designed, rebuilt, diagnosed, improved, mentored |
| **Staff / Lead** | System-level ownership, architecture, technical direction, engineering standards, cross-team influence | designed, drove, aligned, set the pattern for, unblocked |
| **Principal / Architect** | Org-wide technical influence, architecture strategy, large-scale systems, platform modernization, technical standards, technology selection, risk reduction, business alignment | architected, defined, established, standardized, selected, chaired, reduced risk |
| **Distinguished / Fellow** | Enterprise technical strategy, multi-org influence, technology vision, major transformations, engineering culture, long-term direction, industry expertise | set the technical direction for, established across, influenced, shaped |
| **Engineering Management** | Teams, hiring, delivery, engineering effectiveness, strategy, budgets, roadmaps, stakeholders | led, grew, hired, delivered, ran, was accountable for |
| **Executive (VP/CTO/CIO)** | Business outcomes, technology strategy, organizational scale, transformation, financial responsibility, operating models, executive influence, risk and governance, talent strategy | directed, transformed, established, owned the P&L for, oversaw |

**The two failure modes.** A Principal Engineer written with management verbs gets screened as an
EM and rejected by both tracks. A technology executive written with delivery verbs reads as a
senior project manager. Check the verb mix against the target rung before delivering — if the top
five verbs in the document belong to a different rung than the target, the resume is mis-aimed.

**Level inflation is detectable.** Scope claims that outrun the evidence are the first thing a
skeptical recruiter probes. If the target level is a genuine stretch, the honest play is to lead
with the strongest true evidence of that scope, not to relabel everything.

## The positioning sentence

> If the recruiter remembers only one sentence about this candidate, what should it be?

Write it before writing anything else. Test it three ways:

1. **Is it specific enough to be false of someone else?** "Strategic technology leader driving
   digital transformation" is true of a hundred thousand people. Discard it.
2. **Does it name the thing they are unusually good at?** Usually a *combination*: a domain plus a
   technical depth plus a scope. "Principal cloud architect specializing in modernization of
   high-volume financial platforms." "Senior hands-on engineering leader combining distributed
   systems, AWS architecture and enterprise GenAI." "Technology executive who stayed technically
   deep while leading large-scale platform modernization."
3. **Would the candidate agree with it out loud?** If they would hedge, it is wrong.

Then make the whole document serve it: the headline, the summary, which role gets the most bullets,
which bullets lead, what the skills section leads with, what gets compressed to one line.

Content that does not serve the positioning is not neutral — it dilutes. Cut it or shrink it.

## Career story

The resume should show a trajectory: Developer → Senior → Lead → Architect → Principal → technology
leader. Two rules:

- **Never let a promotion disappear.** Two roles at the same employer under one title heading
  erases years of progression. Use the builder's `prior_titles` so the ladder is visible in one
  glance.
- **Non-linear is fine, unexplained is not.** A move that looks like a step down (exec → principal
  IC, big company → startup, management → hands-on) needs one line of context so the reader does
  not invent a worse explanation. A `context` line under the role does this without apologizing.

## Experience and age management

For a long career, the resume is not an autobiography.

- Prioritize the most **relevant** 10–15 years — relevance, not recency, is the criterion.
- Keep earlier experience where it buys credibility (a founding role, a famous system, the origin
  of a domain expertise) — compress it to a line or two under an "Earlier Experience" heading.
- Give older technologies less space unless the target actually wants them. Mainframe depth is
  ballast for an AI-platform role and gold for a modernization role.
- **Never delete experience merely because it is old.** Optimize on relevance. Dropping fifteen
  years to look younger also drops the thing that makes the candidate rare.
- Graduation dates: keep them unless the candidate asks otherwise. Their absence is noticed.

## Title normalization

Respect official titles — inflating one is a reference-check failure waiting to happen. When the
official title misleads (a company where "Engineer IV" means principal, or "Consultant" means
architect), use:

**Official Title | Functional Role**

The builder's `functional_title` field renders exactly this. Never silently substitute the
functional role for the real one.

## Page-length strategy

Not a rule — a budget.

| Situation | Pages |
|---|---|
| Early career | 1 |
| Experienced engineer | 1–2 |
| Senior / Staff / Principal | usually 2 |
| Executive, or a deep technical leader with real range | 2–3 when justified |

A 3-page resume is justified by *content that earns it*, never by career length alone. A page that
is 15% full is worse than cutting to fit — see §8 on `--fit`.

## Job targeting — the 20 steps

When given resume + job description:

1. Parse the resume (forensics pass).
2. Build/refresh the candidate model.
3. Parse the job description.
4. Determine the **true** role requirements — what they are actually hiring, behind the boilerplate.
5. Assess qualitative fit.
6. Identify the strongest matches.
7. Identify weak or missing evidence.
8. Identify the questions worth asking the candidate.
9. Establish positioning for *this* opportunity.
10. Select the relevant accomplishments.
11. Rewrite the summary.
12. Reorder the skills.
13. Select and rewrite the experience bullets.
14. Optimize terminology.
15. Validate factual integrity.
16. Optimize for ATS.
17. Optimize for human readability.
18. Humanize the language (§6, `humanization.md`).
19. Format for the audience.
20. Final quality review (`quality-gates.md`).

### Reading a JD properly

- **Role identity** — what job is this, really? Job titles lie in both directions.
- **Seniority** — what level of influence is expected? Look at who they report to and who they
  influence, not at the years-of-experience line.
- **Critical requirements** — what must be demonstrated. Usually 3–5 things, not the 18 bulleted.
- **Technical, leadership, business, preferred** requirements — separate them; candidates
  over-weight the technical list and under-weight the business one.
- **Hidden signals** — what problem is this hire meant to solve? A JD demanding both greenfield
  design and legacy familiarity is a modernization role. One listing five overlapping tools is a
  team that has not converged. One naming compliance three times is a remediation hire. Position
  to the problem, not to the bullet list.

### Fit classification

Classify every requirement: **Strong Match · Partial Match · Transferable Experience ·
Missing/Unknown · Potential Concern.** Then ask what legitimate resume change would improve the
*perceived* fit — different emphasis, different ordering, an accomplishment currently buried,
terminology that corresponds to theirs. Never manufacture experience to close a gap.

### Do not overfit

Do not copy the posting's wording. The tell is unmistakable to recruiters — they wrote it. Translate
the candidate's real experience into terminology that *corresponds* to the employer's need.

Test: for any phrase in the draft, can you name the candidate experience it came from? If it came
from the posting instead, rewrite it.

Target: *"This person's career naturally fits what we need"* — not *"this resume was rewritten
yesterday to imitate our job description."*

## LinkedIn consistency

When it comes up, compare resume and LinkedIn. Titles must not conflict, dates must align,
responsibilities must be recognizably the same job. The resume can be far more targeted; the two
must not read as different people. A recruiter cross-checks in about ninety seconds.
