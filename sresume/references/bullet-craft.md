# Bullet engineering

SKILL.md §5 is the compact version.

## The shape

**Action + problem + technology/method + scale + result** — as a *checklist of what might be
missing*, never as a template every bullet obeys. A resume where all fourteen bullets follow the
same skeleton reads as generated, and §6 will reject it.

Weak:
> Responsible for cloud architecture.

Better:
> Architected an AWS event-driven platform using Kafka and containerized services to modernize
> transaction processing across multiple product domains, improving scalability and deployment
> independence.

Better still, because it says what the problem *was*:
> Replaced roughly thirty point-to-point integrations between deposits, ledger and fraud with a
> Kafka event backbone, so downstream teams subscribe to account events instead of negotiating a
> new interface each time. Typical integration work dropped from a quarter to about two weeks.

## Deliberate variation

Rotate what each bullet is *about*. A good role block mixes several of these:

- **What was built** — the system, plainly described.
- **A hard problem solved** — the interesting one, with the constraint that made it hard.
- **An architecture decision** — what was chosen, and what it was chosen over.
- **Scale** — the number that makes a reader recalibrate.
- **Technical leadership** — a standard set, a review chaired, a pattern others adopted.
- **Business impact** — the consequence someone outside engineering cared about.
- **Modernization** — what was replaced and what got better.
- **Collaboration** — only when the collaboration was the achievement, not filler.

Also vary *length*. Three long bullets and two short ones read human; five bullets of near-identical
length read machine-made. And vary the opening — not every bullet starts with a past-tense verb;
occasionally leading with the system or the constraint is more natural and more specific.

## Verb registers

Match the register to what actually happened (`forensics.md`, hands-on vs. oversight).

**Hands-on:** built · implemented · developed · designed · prototyped · engineered · wrote · rebuilt
· instrumented · debugged · migrated · optimized

**Technical leadership:** architected · defined · established · standardized · led architecture ·
directed technical strategy · chaired · selected · set the pattern for · aligned

**Executive:** sponsored · directed · transformed · oversaw · established organizational strategy ·
funded · was accountable for

**Avoid** as openers regardless of level, because they are the AI tells: spearheaded · leveraged ·
orchestrated · pioneered · championed · revolutionized · drove (overused to the point of emptiness)
· utilized (use "used").

**Never repeat an opening verb** twice within one role block, or more than three times in the whole
document.

## Metrics

Use them where they exist. Candidates for a number:

revenue · cost savings · cloud spend · latency (p50/p95/p99) · throughput · availability / SLO ·
transactions per day · users · applications migrated · services · teams · engineers · release
frequency · deployment time · lead time · incident count · MTTR · defect escape rate · data volume ·
query time · model evaluation scores · adoption (how many teams actually use the thing)

**Never invent a metric.** Not a rounded one, not a conservative one, not a plausible one.

When a bullet obviously wants a number, flag a **Metric Opportunity** and ask the candidate a
specific question — not "can you quantify this?" but "roughly how many transactions a day did that
platform handle at peak?" Specific questions get answered; vague ones get skipped.

Three rules for numbers that are already there:

1. **Anchor them.** "Reduced latency 40%" means nothing without the baseline. "Cut p99 from 400ms
   to 240ms" is checkable and therefore credible.
2. **Attribute honestly.** If the improvement came from a team of six, "led the work that…" is
   accurate and still impressive. Claiming it solo fails the interview.
3. **Prefer the durable number.** Percentages age; absolute scale does not. "9M transactions/day"
   still lands in five years.

A bullet with no metric is not automatically weak. A bullet with a specific system, a real
constraint and a clear consequence beats a vague one carrying a percentage.

## Technology placement

Do not keyword-dump. If the posting wants AWS, Kafka, Kubernetes, Terraform, Java, microservices,
REST and CI/CD, put each where it genuinely belongs and let the Skills section carry the rest.

Weak:
> Leveraged Kafka, Kubernetes, AWS, microservices, REST APIs, CI/CD and DevOps methodologies to
> drive enterprise transformation.

Better:
> Designed the Kafka event flows between deposit services so downstream applications could consume
> account events without adding more point-to-point integrations.

Always answer, implicitly: **why did this technology exist here?** A technical reader recognizes
genuine experience by whether the technology has a reason. That is also what makes the bullet
survive an interviewer's follow-up question.

## Compression

When a bullet must shrink, cut in this order: adverbs → adjectives → the collaboration clause →
the technology list → the methodology name. Cut the metric and the system name last; they are the
bullet's entire value.

Never compress by merging two accomplishments with a semicolon. That is how a resume acquires the
dense, clause-stacked texture that reads as machine-generated.

## Bullets per role

Roughly: current/most relevant role 4–6 · previous relevant role 3–4 · older relevant role 2–3 ·
early or off-target roles 1–2 or a single summary line. Space allocation is itself a positioning
statement — a reader infers importance from length before reading a word.
