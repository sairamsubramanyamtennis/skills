# Document production — Word, typography and the other output formats

SKILL.md §8 is the compact version.

## The builder

`assets/build_resume.py`. Requires `python-docx` (installed). Never hand-assemble a resume .docx,
and do not route a resume through the generic `docx` skill — this builder encodes the ATS
constraints that matter and the generic path does not.

```bash
cd ~/.claude/skills/sresume/assets
python build_resume.py --schema                                   # full input format
python build_resume.py resume.json -o out.docx                    # default preset
python build_resume.py resume.json -o out.docx --preset executive
python build_resume.py resume.json -o out.docx --fit 2            # squeeze toward 2 pages
python build_resume.py resume.json -o out.docx --margin 0.6 --body 10
python build_resume.py resume.json --txt ats.txt --md linkedin.md
```

`assets/example_resume.json` is a working reference showing every section type, `prior_titles` for
promotions, `functional_title` for title normalization, inline `**bold**`, and a role `context`
line.

**File layout.** JSON source in `C:\Users\ssair\resumes\src\<Name>_<Variant>.json`, built documents
in `C:\Users\ssair\resumes\out\`. The JSON is the artifact worth keeping — every format
regenerates from it, and diffing two variants' JSON is how you catch factual drift (§34).

**Naming** (SKILL.md §34 / `memory/versions.md`): `Sai_Master`, `Sai_Principal_Architect`,
`Sai_Principal_Engineer`, `Sai_AI_Architect`, `Sai_VP_Technology`, `Sai_<Company>_<Role>_<YYYY-MM>`.

## What the builder guarantees, and why

Do not "improve" these away.

| Constraint | Reason |
|---|---|
| Single column, no tables | Multi-column and table layouts are the #1 cause of scrambled ATS parses — two columns often extract as interleaved nonsense |
| No text boxes, no images, no shapes | Most parsers do not read them at all; content in them is invisible to the ATS |
| No content in headers/footers | Frequently dropped entirely. Contact details in a header can vanish |
| Real uppercase section headings | Section detection ("EXPERIENCE", "EDUCATION", "SKILLS") drives how a parser buckets your content |
| Right tab stop for dates, in the same paragraph | Keeps role + company + dates as one logical line for the parser, while typesetting properly. A space precedes each tab so naive extractors that drop `<w:tab>` still see a word boundary |
| `keep_with_next` on headings and role blocks | No section heading stranded alone at the foot of a page |
| Widow/orphan control on every paragraph | No single line of a bullet split across a page break |
| `noProof` on technology-dense lines | Suppresses Word's red squiggles under Kafka, Kubernetes, pgvector — the document looks finished when the user opens it |
| Explicit `w:rFonts` for ascii/hAnsi/eastAsia/cs | Otherwise Word silently substitutes Times New Roman for some glyphs |

## Presets — typography only

A preset never edits words. Content selection and ordering are the persona's decisions.

| Preset | Font | Body | Accent | Use for |
|---|---|--:|---|---|
| `ats` | Calibri | 11.0 | black, no rules | Unknown or old ATS; when parseability beats appearance |
| `recruiter` | Calibri | 10.5 | navy | **Default.** Scannable, quietly modern, safe everywhere |
| `technical` | Calibri | 10.0 | navy | Engineers who need systems detail on the page; denser |
| `principal` | Georgia | 10.0 | navy | Principal / architect; serif, more air, authoritative |
| `executive` | Georgia | 10.5 | navy | Executive; generous white space, restrained, fewer heavier lines |
| `consulting` | Calibri | 10.5 | navy | Client-facing profile |

Any preset field can be overridden per-document in the JSON `style` block (`font`, `body`, `name`,
`heading`, `accent`, `rules`, `space_after`, `section_before`, `bullet_space`, `headline_caps`,
`margin_in`).

## The six presentation styles — what changes is CONTENT

The preset is the typography half. This is the half you decide.

**ATS resume** — conservative, standard headings, single column, clear chronology, minimal
emphasis. Skills section carries keyword coverage.

**Recruiter resume** — optimized for a fifteen-second scan. Strong hierarchy, selective emphasis,
positioning stated at the top, the strongest three bullets first in the top role.

**Technical hiring manager resume** — systems, technologies, architecture, scale, technical
decisions, engineering impact. More technical specificity per bullet; the *why* behind each choice.

**Principal / architect resume** — architecture, cross-team influence, technical strategy, platform
evolution, standards, the major systems. Scope of consequence over delivery detail.

**Executive resume** — strategy, transformation, organizational impact, business outcomes,
leadership scale, financial impact. Compress the technology; expand the consequence.

**Consulting / client resume** — expertise, major engagements, industry knowledge, transformation
capability, client outcomes. Engagements may lead over employers.

## Page count and rendered inspection

`build_resume.py` prints a **text-metric estimate**, not a layout result. It is useful while
drafting and is typically within ~10% — but never quote it as the page count.

**Microsoft Word 2016 and pywin32 ARE installed on this machine**, so the real numbers are
available. Always confirm with `page_check.py` before reporting a length:

```bash
python page_check.py resume.docx                     # real pages/words/lines
python page_check.py resume.docx --pdf out.pdf       # export a PDF
python page_check.py resume.docx --png render/       # one PNG per page
python page_check.py legacy.doc --docx modern.docx   # convert a .doc
```

It reports Word's true page count, how full the **last page** is (the "page that is 11% full"
problem), and the first line of every page so you can see exactly where the breaks land.

**Then actually look at it.** Render to PNG and read the images before delivering. That is the only
way to satisfy §21 — a technically valid .docx that looks amateurish is the failure this catches.
Check: page breaks · headings stranded at a page foot · bullets split across pages · alignment ·
consistent section spacing · a final page that is nearly empty.

`--png` needs `pypdfium2` (installed). If Word is ever unavailable, `page_check.py` says so and
exits; fall back to the estimate and **state plainly that you could not see the rendered page**
rather than implying you checked.

An earlier version of this file claimed there was no Word automation here. That was wrong — the
COM path works, and there is no reason to ship a resume you have not looked at.

If it runs long, `--fit N` walks a bounded ladder (margins 0.75″→0.55″, body size down to −1.0pt).
When it reports it could not reach the target, **cut content**. Typography past that point looks
cramped, and a cramped resume reads as someone who could not bear to cut anything.

Watch for the opposite failure too: a second page that is 10% full. Either cut to one page or add
enough substance to justify the second. The builder flags this.

## The other output formats

| Format | How |
|---|---|
| **Word (.docx)** | `-o out.docx` — the primary deliverable |
| **PDF** | Build the .docx; the user exports from Word (File → Save as PDF). Do not ship a PDF built by a converter that is not on this machine |
| **Plain-text ATS** | `--txt` — no tabs, no bullet glyphs, safe to paste into a web form textarea |
| **LinkedIn** | `--md`, then rewrite for LinkedIn's register: first person, warmer, no contact block, About section ≈ 3 short paragraphs, experience entries shorter than the resume's |
| **Executive biography** | Prose, third person, 200–400 words, one page. Career arc, scope, two or three signature accomplishments, current focus |
| **Recruiter submission** | Resume plus a short positioning cover note naming the fit in three bullets |
| **Internal promotion packet** | Evidence organized against the *promotion criteria*, not against a job market. Scope, influence, impact, and what changed since the last level |
| **Consulting profile** | Engagements over employers; industries, outcomes, and the specific expertise being sold |
| **One-page profile** | Positioning, three to five signature accomplishments, core skills, current role. Not a squeezed resume — a different document |

## When a resume arrives as a file

`.docx` in — there is no pandoc here, so read it with python-docx:

```bash
python -c "import docx,sys; print('\n'.join(p.text for p in docx.Document(sys.argv[1]).paragraphs))" resume.docx
```

That misses text in tables, which is exactly where badly formatted resumes hide half their content.
If the output looks suspiciously short, also walk `doc.tables`. A resume whose content lives in
tables is itself a finding — report it as an ATS red flag.

`.pdf` in — use the `pdf` skill to extract, then note that you are working from extracted text and
may have lost formatting nuance.
