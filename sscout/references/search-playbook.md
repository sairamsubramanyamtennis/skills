# Sscout — search playbook

Read this before the first scan of any company. SKILL.md §2 is the compact rule; this is the
mechanics.

---

## STEP 1 — Find the authoritative source

Rank sources in this order and say which one you used:

1. **The company's own ATS instance** — the system actually holding the requisitions. This is
   ground truth: it has the complete list, the live status and the real apply link.
2. **The company careers site** — usually a skin over the ATS. Good, but marketing pages sometimes
   surface only "featured" roles.
3. **The company's LinkedIn jobs tab** — decent completeness, weaker on description detail and
   often stale by days.
4. **Third-party aggregators** (Indeed, ZipRecruiter, Dice, Glassdoor, Levels.fyi job boards) —
   **discovery only**. Use them to learn that a role exists, then find the first-party posting and
   link to that. If you cannot, flag **Current status uncertain**.

How to find the ATS: fetch the careers page and look at where the "search jobs" / "apply" links
point. The hostname tells you the system.

| ATS | Host pattern | Search mechanics worth knowing |
|---|---|---|
| Workday | `<co>.wd1.myworkdayjobs.com/<site>` | Facets in the URL path; a JSON endpoint at `.../jobs` accepts POST with `searchText`, `limit`, `offset`. Paginates 20 at a time — **always page through to the end**. |
| Greenhouse | `boards.greenhouse.io/<co>`, `job-boards.greenhouse.io` | `/embed/job_board?for=<co>` lists everything on one page. Small companies list all roles with no search box — read the whole list. |
| Lever | `jobs.lever.co/<co>` | Full list on one page, grouped by team. `?mode=list` flattens it. |
| Ashby | `jobs.ashbyhq.com/<co>` | Single page, client-rendered; if fetch returns an empty shell, search the site via a search engine instead. |
| SmartRecruiters | `careers.smartrecruiters.com/<co>` | Public API: `api.smartrecruiters.com/v1/companies/<co>/postings`. |
| iCIMS | `careers-<co>.icims.com` | Keyword + radius search; radius defaults small — **widen it or set Remote explicitly**. |
| Taleo / Oracle | `<co>.taleo.net`, `<co>.oraclecloud.com` | Legacy, brittle search. Broad single-word queries work better than phrases. |
| SuccessFactors | `career<n>.successfactors.com` | Facet-heavy; location facet often excludes remote roles from a city search. |
| Eightfold / Phenom | `<co>.eightfold.ai`, `<co>.phenompeople.com` | AI matching — the *same* query returns different results with different session state. Run each query twice if results look thin. |

Also check: subsidiary and acquired-brand careers sites (they often keep separate ATS instances),
and any "campus / experienced / executive" split in the navigation. Executive roles are frequently
on a **separate** board that the main search does not cover.

---

## STEP 2 — Enumerate the company's title ladder before searching for titles

The point of this step is to learn the vocabulary you should be searching for.

- If total openings are small (under ~200), **list them all** and read the titles. That is the
  cheapest complete answer and it hands you the ladder directly.
- Otherwise, discover the ladder: search one generic anchor term ("engineer", "architect") and read
  the returned titles for the company's own level words — *Member of Technical Staff*, *Technical
  Staff Member*, *Consulting Engineer*, *Engineer IV*, *Band 8*, *Grade 62*, *Expert*, *Master*,
  *Chief Engineer*, *Senior Manager, Software Engineering*.
- Cross-check with a public source: levels.fyi, Blind, or the company's engineering blog often name
  the ladder explicitly.
- Record what you learn in `memory/companies.md`. Next scan starts from the vocabulary, not from
  scratch.

**Known in-house equivalents to Principal/Distinguished** (non-exhaustive, extend as you learn):
Member of Technical Staff / MTS / Principal MTS / Senior MTS (Oracle, Salesforce, VMware, AMD,
Nvidia) · Senior Technical Staff Member, STSM (IBM) · Distinguished Technologist, Chief Technologist
(HP/HPE) · Consulting Member of Technical Staff (Oracle) · Chief Architect, Chief Engineer
(defense/aero) · Technical Fellow (Microsoft, Boeing) · Engineer/Architect + roman numeral or
number bands (banks, insurers, healthcare) · Expert Engineer, Master Engineer (European firms) ·
Senior Vice President, Technology (banks — often an IC or small-span role, **not** an executive
role; check scope before you assume).

**Banking/financial-services caveat**: "Vice President" and "Director" are pay grades, not
management jobs. A "VP, Software Engineering" at a bank is frequently a hands-on senior IC.
Judge by the responsibilities, always.

---

## STEP 3 — Run the query bank

Run the seven bands in SKILL.md §2. For each band:

- Query the ATS search box **and**, where the ATS supports it, the description body — many roles
  never say "architect" in the title but say "own the architecture" in the body.
- Try **singular and plural, abbreviated and expanded**: AI / artificial intelligence, GenAI /
  generative AI, ML / machine learning, K8s / Kubernetes, obs / observability.
- Try **location-free** queries. A location filter is the single most common cause of missing a
  remote role that is nominally "headquartered" elsewhere.
- Then run location variants explicitly: Remote, Remote - US, Texas, Dallas, Plano, Richardson,
  Irving, Fort Worth, Frisco, Addison, Westlake — plus the company's own DFW-area campus names.

Search-engine fallback when the ATS search is broken or client-rendered:
`site:<ats-host>/<company> "principal"`, or `"<company>" "distinguished engineer" careers`.
Treat the results as discovery and verify each one on the employer site.

**Log the total posting count.** "412 open roles, 63 in engineering/technology, 11 at target level"
is a far more honest coverage statement than a list of hits.

---

## STEP 4 — Triage, then read

- **Triage on title + location + team** to a candidate set. Be generous here; the cost of reading
  one extra JD is low, the cost of missing a role is high.
- **Read the full description** for anything that could plausibly be at level, anything with an
  ambiguous title, and everything you intend to recommend. Never score from a title and a
  three-line search-results snippet.
- Capture from each JD: required years, scope words (team / org / enterprise / company-wide),
  reporting line, architecture ownership, pay band, work style, travel %, clearance, and whether it
  is a backfill or a new function (new functions carry more shaping room and more risk).

---

## STEP 5 — Verify freshness

- Prefer a posted/updated date from the employer site. Note it.
- No date shown: check whether the job ID appears in the ATS's current listing at all — if the ATS
  returns it in a live search, it is live.
- Flag ⚠️ **Posting may be stale** when: the description references a past date, the requisition ID
  is far below neighbouring IDs, or the role appears only on aggregators.
- Evergreen/pipeline postings ("we are always looking for...") are real but low-yield. Say so
  rather than ranking one first.

---

## STEP 6 — Write the dossier

Before returning the answer, update `memory/companies.md` with: ATS and URL patterns, total
postings, the in-house title lexicon learned, level-ladder notes, the DFW/remote posture, comp
disclosure practice, and the list of postings seen (ID + title + fit score). The next
`Check again next week` is a diff against exactly that list — it only works if you wrote it.

---

## Scaling note

If Sai has explicitly asked for parallel/multi-agent work, one subagent per search band (or per
company, on a multi-company sweep) is a good fan-out — each returns a compact list of
`title | id | location | url`, and you do the reading and scoring yourself. Do not fan out
unprompted; a single-company scan is comfortably a solo job.
