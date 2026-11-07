# Resume forensics — the read-before-writing pass

SKILL.md §2 is the compact version. This is the working procedure. Run it whenever an existing
resume enters the conversation, even if the user only asked for a small change — a "quick tweak"
requested on a badly positioned resume is wasted work.

## The twenty questions, and what each is diagnosing

Do not answer these on the page. Answer them for yourself, then write the §11 output contract.

**Identity and level**
1. What does this person *actually do* all day? (Not their title. What work.)
2. What level are they operating at today?
3. What level could they credibly compete for? — the gap between 2 and 3 is where the value is
4. What are the strongest technical domains?
5. What business domains do they understand? — often the real differentiator, usually buried
6. What differentiates them from a hundred similar résumés?
7. What career trajectory does the document show — and does it show one at all?

**Content defects**
8. Which accomplishments are buried in the middle of a bullet or the bottom of a role?
9. Which bullets describe responsibilities rather than impact?
10. Which technologies are understated relative to how much they were actually used?
11. Which technologies are overstated — listed but barely evidenced?
12. Where is leadership demonstrated (as opposed to claimed)?
13. Where is technical depth demonstrated?
14. Where is scale demonstrated?
15. Where are measurable outcomes missing but clearly available?
16. What repeats — the same accomplishment told three times across three roles?
17. What is outdated and taking space?
18. What actively *weakens* perceived seniority? (See the list below.)

**Gaps**
19. What important capability can reasonably be inferred but needs confirmation?
20. What would a skeptical recruiter question?

## Things that silently lower perceived seniority

Watch for these in Q18 — candidates almost never see them:

- Tool-level bullets at a senior level ("used Jira to track tasks", "attended daily standups").
- Passive scope language: *assisted with*, *participated in*, *involved in*, *helped to*, *worked
  with the team to*.
- Listing certifications or coursework above experience past ~10 years of career.
- A skills section led by things everyone has (Microsoft Office, Windows, Agile).
- Equal space given to a 2-year junior role and a 7-year principal role.
- Team-scale language where org-scale language is true ("worked with two developers" when they set
  a standard four teams adopted).
- Titles without functional clarification when the company's ladder is non-obvious.
- A summary that would fit anyone at any level.
- Bullets ending in the technology rather than the consequence.

## The candidate model

Out of the pass, build and keep this. It is the factual foundation for every variant, and it lives
in `memory/master-career-resume.md`.

| Field | Note |
|---|---|
| Current level | What they are, today, by the ladder in `positioning.md` |
| Likely market level | What they can credibly compete for |
| Primary professional identity | The one-line answer to "what are you" |
| Secondary identities | The other credible framings — these become resume variants |
| Technical domains | With depth, recency, duration |
| Architecture experience | Which kind: software / solutions / enterprise / platform / cloud / data / integration / AI |
| Cloud experience | Provider, depth, production vs. evaluation |
| AI / data experience | **Production or experimental?** Recruiters test this one |
| Hands-on engineering | How recent, how deep, what they personally built |
| Leadership scope | People, teams, orgs, or influence without authority |
| Business domains | Industry and regulatory knowledge |
| Major programs | The three or four things they are actually known for |
| Scale | Users, transactions, services, teams, spend, data volume |
| Quantifiable outcomes | Every number they can defend |
| Certifications / education | With dates |
| Differentiators | The unusual combination |
| Weaknesses | Honest, including the ones they will be asked about |
| Target-role compatibility | Per target family |

## Skill discovery — three registers

Resumes underrepresent people, so read project descriptions for capability, not just for keywords.
"Built Kafka pipelines" may evidence event-driven architecture, distributed systems, streaming
data, integration architecture, scalability work and reliability engineering.

But grade every skill before it goes on a page:

- **Explicit** — the resume or the candidate states it. Use freely.
- **Strongly evidenced** — the described work demonstrably requires it. Use, and be ready to point
  at the evidence if challenged.
- **Possible** — plausible given the environment, but unconfirmed. **Never present as fact.** Ask
  when confirming it would materially strengthen the resume; drop it silently when it would not.

The skills inventory covers languages · frameworks · cloud · architecture · data · AI/ML/GenAI ·
DevOps · observability · security · databases · messaging · platforms · engineering practices ·
leadership · business domains. For each important skill, know depth, recency, duration, production
vs. experimental, hands-on vs. oversight, scale, and the accomplishment that backs it.

**Do not produce keyword dumps.** An inventory is what you know; the resume shows a curated subset.

## Hands-on vs. oversight

The single most common credibility failure in senior resumes. Establish, per accomplishment, which
of these is true:

| Reality | Verbs that are honest |
|---|---|
| Personally designed the system | designed, architected (if the design was theirs) |
| Personally wrote important code | built, implemented, developed, engineered, wrote |
| Built a prototype or PoC | prototyped, built, proved out |
| Reviewed others' architecture | reviewed, advised, approved, chaired |
| Set technical direction | defined, established, standardized, led architecture, directed |
| Led the engineers who did it | led, managed, grew, ran |
| Funded or sponsored it | sponsored, funded, championed (rare, but honest here) |
| Ran the org that owned it | oversaw, directed, transformed, established |

A Principal Engineer whose bullets all read *oversaw* will be screened as a manager. A manager
whose bullets all read *built* will fail the technical interview. Ask when it is unclear — this is
worth an explicit question more often than almost anything else.

## Output

The forensics pass produces the §11 contract, not a rewrite. Resist rewriting until the positioning
question in §3 has an answer. Beautifying a resume that is aimed at the wrong level is the most
expensive mistake available here.
