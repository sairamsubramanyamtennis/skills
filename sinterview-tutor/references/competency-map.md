# Competency map — decomposing a JD into what the interview will actually test

SKILL.md §4 is the compact version. Read this before building the first map for an engagement.

The map exists to do one thing: **refuse to treat every line of the job description equally.** A JD
is written by a hiring manager and a recruiter and an HR template, and roughly a third of it is
boilerplate that no interviewer will ever ask about. Prep built on an unweighted JD is prep spread
evenly across noise.

---

## The twelve categories

Every meaningful requirement goes into exactly one. If a requirement seems to fit two, ask what the
interviewer would actually be testing and put it there.

| Category | What it covers | How it gets tested |
|---|---|---|
| **Architecture** | Distributed systems, microservices, event-driven, API architecture, integration, target-state design, architecture governance | Discussion, whiteboard, "walk me through a system you designed" |
| **Technical Depth** | Named technologies: Java, Python, Kafka, AWS, Kubernetes, Postgres, DynamoDB, Snowflake | Concept questions, "how does X actually work", troubleshooting |
| **System Design** | The ability to design something new under constraints | A 45-60 min design round |
| **Data** | Data mesh, streaming, lakes, warehouses, modelling, governance, lineage | Design + concept |
| **AI / GenAI** | LLM applications, RAG, agents, vector DBs, MCP, AI platforms, AI governance, evals | Design + concept + "what have you actually shipped" |
| **Cloud** | AWS/Azure/GCP services, cloud-native patterns, migration, cost, multi-region | Concept + design |
| **Security** | AuthN/AuthZ, IAM, encryption, secrets, threat modelling, regulated-industry controls | Scenario + design attack |
| **Reliability & Ops** | Observability, SRE, resilience, DR, HA, incident response, capacity | Scenario, troubleshooting, "tell me about an outage" |
| **Leadership** | Technical influence, architecture decisions, mentoring, standards, stakeholder management, org change | Behavioral + scenario |
| **Behavioral** | Conflict, failure, collaboration, ownership, ambiguity, values | STAR questions |
| **Domain Knowledge** | Banking, payments, deposits, wealth, trading, insurance, healthcare, retail | Woven into everything; often the real differentiator |
| **Coding (light)** | Code reading, implementation reasoning, take-home review, API/class design | "How would you implement this", code walkthrough |

---

## The depth ladder

What the role needs, not what would be nice.

| Depth | Test | Prep implication |
|---|---|---|
| **Awareness** | Can define it and say when it applies | 10 minutes of reading |
| **Working Knowledge** | Can use it correctly and describe a real usage | One tutor session |
| **Deep Expertise** | Knows the failure modes, the tuning knobs, the operational reality | Multiple sessions + a design exercise |
| **Architect-Level** | Can choose it over alternatives, defend the choice under attack, and say when it is the wrong answer | Sessions + design + red team |

Read the depth from the JD's verbs. "Familiarity with Kafka" is Awareness. "Experience building
event-driven systems with Kafka" is Working Knowledge. "Own the firm's streaming architecture" is
Architect-Level. Interviewers calibrate to the verb too.

---

## Probability signals

These raise interview probability. Weight them in this order:

1. **In the title.** A "Cloud Architect" title makes cloud Very High regardless of the body.
2. **Repeated across sections.** A technology in responsibilities *and* required *and* preferred is
   what the hiring manager is actually worried about.
3. **First three responsibility bullets.** JD bullets are usually ordered by real priority.
4. **Attached to a named system or initiative.** "Modernize the settlement platform" is a specific
   problem someone will ask him to solve out loud.
5. **In the required (not preferred) list, with years attached.** Years attached means screening.
6. **Named in the team or org description.** The team's charter predicts the panel's interests.
7. **Unusual or specific.** Generic "strong communication skills" is boilerplate. "Experience
   presenting architecture to risk committees" is a real question waiting to happen.

These lower it:

- Appears once, in the preferred list, with no elaboration.
- Part of an obvious template block (the identical "equal opportunity / physical requirements /
  ability to work in a fast-paced environment" paragraphs).
- A laundry list of eight technologies in one bullet — nobody probes all eight; they probe the one
  that matters to the team, so ask which one the recruiter emphasized.

---

## Reading a thin JD

Some postings are four bullets long. Do not compensate by inventing requirements. Instead:

1. **Say the JD is thin, explicitly**, and label the whole map as inference.
2. **Anchor on the title and level.** A Principal Architect loop has a predictable shape even when
   the JD does not.
3. **Anchor on the company and the team.** Research the engineering stack from public sources
   (engineering blog, tech talks, job postings for *adjacent* roles on the same team — those are
   often far more detailed) and cite what you found with an as-of date.
4. **Ask Sai** what the recruiter said. Recruiter intel routinely beats the JD.
5. **Widen the map and lower confidence** rather than narrowing it and being wrong. A thin JD means
   more Medium-probability entries, not fewer.

---

## Output shape

```
## Competency map — <Company> <Role>
Source: <JD URL / pasted, dated> · Level read: <level, evidence>

| # | Competency | Category | Importance | Probability | Depth needed | Format | Evidence |
|---|---|---|---|---|---|---|---|
| 1 | Event-driven architecture at scale | Architecture | Critical | Very High | Architect | Design + attack | "own the target-state event architecture" (resp. #1); Kafka in required + preferred |
...

**Boilerplate excluded:** <what you dropped and why — proves you read the whole thing>
**Open questions:** <what you could not determine without asking>
```

The "boilerplate excluded" line matters. It is the evidence that the weighting was a judgment and
not an omission.

---

## Change log

| Date | Change |
|---|---|
| 2026-08-29 | File created with the skill. |
