# New Skill Design Template

Fill this out **before** invoking `skill-creator`. Present the CAPABILITY GAP block (below) to Sai
and get approval first — creating a permanent skill is a SYSTEM CHANGE under §10.

---

## Step 0 — The approval block

```text
CAPABILITY GAP

Why it exists:

Existing alternatives:

Proposed capability:

Why it should be permanent:

Expected benefit:
```

Do not skip this even when the gap feels obvious. If you cannot fill "Existing alternatives"
honestly, you have not done discovery (§7).

---

## Step 1 — The seven questions (§4)

Answer each in one line. If three or more push toward "no", stop and use a temporary agent.

1. Does an existing skill already perform this function?
2. Can an existing skill reasonably be extended?
3. Is this likely to be needed again?
4. Is the domain sufficiently specialized?
5. Would separation improve quality?
6. Would creating it reduce duplication?
7. Does it deserve its own memory or workflow?

---

## Step 2 — The design

### NAME
House convention: persona skills are `s` + role (`sarch`, `sscout`, `sresume`, `smob-dic`,
`sinterview-tutor`, `suffet`, `sagent`). Mechanical skills are plainly named
(`quantitative-momentum`, `qm-recon`, `pg-skill`).

### PURPOSE
One paragraph. What this skill exists to do, stated so a stranger could tell it apart from every
neighbouring skill.

### WHEN TO USE
Concrete triggers, including the casual phrasings Sai actually types — not just the formal ones.
This becomes the front half of the YAML `description`, which is the only thing the router sees.

### WHEN NOT TO USE
Name the neighbouring skills explicitly and say what goes there instead. This is what prevents
overlap, and it belongs in the `description` too.

### EXPERT PERSONA
Who the skill is. Level, background, standards, temperament, and what it refuses to do.

### INPUT CONTRACT
What the skill needs to start. What it must ask for when missing — and it must ask rather than
invent.

### OUTPUT CONTRACT
The shape of a finished answer. Sections, ordering, scoring scale if any, file deliverables.

### TOOLS / RESOURCES
Scripts, databases, APIs, reference files, subagents. Note entitlements and known limits (e.g.
Gmail MCP is draft-only; Polygon history starts 2003-09-10).

### RESEARCH STANDARD
What counts as evidence here. Source hierarchy, what must be verified live vs. recalled, what gets
labelled as an assumption, and the falsification bar.

### MEMORY REQUIREMENTS
`memory/` files the skill owns, what gets written when, and what belongs in the user's auto-memory
instead. Prefer `lessons.md` + one domain file over a sprawl.

### INTERACTION WITH OTHER SKILLS
Who it calls, who calls it, and where the handoff boundary sits.

### QUALITY CHECKS
The self-review the skill runs before returning. Make these checkable, not aspirational.

### FAILURE CONDITIONS
How this skill fails badly, and the guardrail for each. Every real failure observed later gets
appended here.

---

## Step 3 — Build it

1. Draft the folder: `SKILL.md`, `references/`, `memory/`, `scripts/` as needed.
2. Invoke `skill-creator` to author and validate, and to tune the `description` for triggering.
3. Add the entry to `skills_registry.md`.
4. Note in `sagent/memory/lessons.md` what gap prompted it — so skill health (§8) can later judge
   whether it earned its place.
