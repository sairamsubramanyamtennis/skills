# Jyotish Reader — Mundane Astrology Reference (mundane-astrology.md)

> Working reference for questions about nations, collective events, weather and markets
> treated strictly as a mundane subject. Read in full before any mundane statement.
> Same house rules as `../instructions.md` §7A/§7B and Lessons 38–39: **state what the chart
> shows and stop.** Built 2026-10-09 by jyotish-agent (approved by Sai). Status: v1.

**Status markers used in every mundane output:**
- **[classical]** — rule stated in a named classical text, with chapter/verse.
- **[tradition]** — standard panchanga or modern-Indian practice; source named, not verified against a primary text.
- **[synthesis]** — natal rules extended to an entity by analogy. Defensible, not classical.
- **[exploratory]** — this file's own working rule. Uncalibrated until analogues accumulate.

Mundane work has far fewer validated precedents than natal work. Every mundane finding is
**exploratory unless it carries a [classical] tag AND a matched historical analogue.**

---

## 1. Classical Sources and What Each Contributes

Jyotisha has three branches (skandhas): **Hora** (nativities), **Ganita** (astronomy/mathematics)
and **Samhita** (collective/omen/mundane). BPHS Ch. 1 śl. 1–4 (Santhanam Vol. 1, in
`../texts/`) names all three and says Parashara is teaching Hora. **Mundane astrology is the
Samhita branch.** BPHS is a natal text: it supplies tools, not mundane doctrine.

| Source | What it contributes | Status |
|---|---|---|
| **Brihat Samhita** (Varahamihira, 6th c.; tr. N. Chidambaram Iyer 1884, on wisdomlib) | The core mundane text. Ch. 3–10 the "courses" (chara) of Sun, Moon, Rahu, Mars, Mercury, Jupiter, Venus, Saturn: each planet's transit by nakshatra/sign mapped to regions, crops, rulers. Ch. 11 comets (ketu). Ch. 14 **Kurma Vibhaga**: the nakshatras assigned in groups to the nine regions of Bharatavarsha (the classical "which land does this affect" table). Ch. 15 nakshatra-vyuha (what each nakshatra rules). Ch. 17 **graha-yuddha** (planetary war). Ch. 18 Moon's conjunctions with planets. Ch. 19 graha-varshaphala (the year ruled by each planet). Ch. 20 graha-shringataka (planetary groupings). Ch. 21–23 rain/weather (garbha). Ch. 32 earthquakes. Ch. 46 utpata (portents, public calamity). | [classical] |
| **Brihat Samhita Ch. 5, Rahu-chara** (eclipses) | v. 8–11: eclipses are the Moon entering the Earth's shadow and the Moon covering the Sun; Varahamihira sets aside Rahu as the physical cause. v. 18, 25: eclipses are computed, and a competent calculation "will at no time fail". **v. 35–42: effects by the sign the eclipse falls in, with peoples/regions per sign; v. 42 defers to Kurma Vibhaga for the nakshatra.** v. 63: with portents, the effects recur at 6/12/18/24/30/36 months. v. 69–80: effects by lunar month. v. 97–98: a solar eclipse on the amavasya after a lunar eclipse = discord; a lunar eclipse on the purnima after a solar eclipse = good fortune. | [classical] |
| **Brihat Samhita Ch. 8, Brihaspati-chara** | Jupiter's years are named from the nakshatra of his heliacal rising; the **60-year samvatsara cycle** (Prabhava first, when Jupiter rises at the start of Dhanishta in Magha). Each samvatsara carries stated collective results. | [classical] |
| **Narada Samhita** (verses as quoted by Drik Panchang, "Samvat Mantri Mandala") | The **cabinet of the year**: Raja = lord of the weekday of Chaitra Shukla Pratipada; Mantri = lord of the weekday of Mesha Sankranti; Sasyesha = Karka Sankranti; Rasesha = Tula Sankranti; Niresha = Makara Sankranti; Durgesha/Senadhipati = Simha Sankranti; Meghesha (rain) = weekday of the Sun's entry into Ardra. | [classical], verses quoted second-hand; Meghesha [tradition], no verse cited |
| **Agni Purana Ch. 128, Kota-chakra** | A "fort" diagram of nested squares for forecasting the outcome of siege/conflict. | [classical] existence verified; mechanics in §3 are [tradition] |
| **Narapati Jayacharya, *Svarodaya*** (Narapati son of Amradeva, Anahilapataka, 1176 CE) | War-divination with chakras (diagrams) for a king's victory. Modern expositions place the Kota chakra here. | [tradition]; attribution of the Kota chakra to this text not verified |
| **BPHS** (Santhanam Vol. 1–2, in `../texts/`) | Tools borrowed by analogy: house significations Ch. 12–23 (one chapter per house), Vimshottari, Ashtakavarga, special lagnas. Vol. 2 Ch. 91: effects and remedies of birth during an eclipse (natal). The upagraha list names **Utpata**, "a portent boding public calamity like an eclipse, earthquake". | [classical] for natal use; [synthesis] applied to an entity |
| **Tajika / Varshaphala** (Nilakantha, *Tajika Nilakanthi*, 16th c.) | The annual return chart (Sun back on its natal sidereal longitude), Muntha, year lord. Natal by design; applied to a foundation chart as the national annual chart. | [synthesis] |
| **Great-conjunction doctrine** (Masha'allah; Abu Ma'shar, *On the Great Conjunctions*) | The ~20-year Jupiter–Saturn conjunction, the ~240-year triplicity "mutation", Aries-ingress charts. **Perso-Arabic and tropical, not jyotish.** Jyotish's own counterpart is the Jupiter samvatsara cycle (BS Ch. 8): 60 years ≈ three Jupiter–Saturn synodic cycles (3 × 19.86 = 59.6 yr). | [tradition, non-Indian]; cite as such |
| **B.V. Raman, *Mundane Astrology*** | The standard modern Indian synthesis (national houses, Mesha Sankranti charts). **Not on file in `../texts/`.** Cite only if the book is supplied. | not on file |

**Source hierarchy for mundane questions:** Brihat Samhita > Narada Samhita > BPHS (by analogy) >
modern synthesis > Perso-Arabic/Western doctrine. When they disagree, show both (instructions §2).

---

## 2. Casting and Reading a National / Entity Chart

### 2.1 Which chart (in order of preference)
1. **Foundation chart**: the moment sovereignty or legal existence took effect, cast for the
   capital or the place of the act. Midnight-effective acts (India 1947) use the legal instant.
2. **Mesha Sankranti chart** for the capital: the annual chart of the land when no reliable
   foundation time exists, and the annual overlay when one does. [tradition]
3. **Chaitra Shukla Pratipada chart**: the samvatsara chart; gives the Raja of the year. [classical, Narada Samhita]
4. **Event charts**: eclipses, lunations, great conjunctions, cast for the capital.

### 2.2 Conventions (same as natal unless stated)
- Lahiri ayanamsa, whole-sign houses, `scripts/compute_chart.py`. **Record the node type**
  (true vs mean). A disputed foundation time plus a node change can move a whole house.
- **Disputed foundation time:** run every variant. **Report only what is robust across the
  variants**; anything that depends on one variant's lagna is [exploratory] and the variant is
  named. Never pick the variant that "works" after the fact.
- The **Moon sign** of the foundation chart anchors national Sade Sati and Vimshottari.

### 2.3 House significations for a nation [synthesis: BPHS Ch. 12–23 natal meanings extended to an entity, as in modern Indian practice]
| House | Signifies for the nation |
|---|---|
| 1 | The nation as a whole, its people's general condition, national character and vitality |
| 2 | Treasury, public revenue, national stores of food and wealth, the state's speech/press |
| 3 | Communications, transport, media, neighbouring states, near borders |
| 4 | Land, agriculture, mines, housing, the homeland, mass education, the mood of the populace |
| 5 | Birth rate and children, education, culture, entertainment, sport, intellectual life |
| 6 | Standing armed forces, police, civil service, public health and disease, labour, internal enemies, debt |
| 7 | Foreign relations, treaties, open adversaries and war, foreign trade partners |
| 8 | Mortality and death rate, disasters, hidden crises, foreign debt, unearned/inherited assets |
| 9 | Judiciary, religion, higher learning, long-distance shipping and travel, dharma of the state |
| 10 | Government, head of state, ruling authority, national prestige |
| 11 | Legislature, allies, gains, the fulfilment of collective aims |
| 12 | Expenditure, losses, prisons and hospitals, espionage and secret enemies, emigration |

### 2.4 Graha karakas in mundane work [synthesis from the BS chara chapters + BPHS Ch. 3]
Sun: head of state, central authority · Moon: the public, masses, food, water · Mars: army,
police, fire, conflict, engineering · Mercury: trade, communications, media, clerks · Jupiter:
judiciary, religion, counsel, prosperity · Venus: arts, women, luxury, crops, alliances · Saturn:
labour, the poor, land, old institutions, scarcity, delay · Rahu: foreigners, epidemics,
upheaval, new technology · Ketu: sudden rupture, separatism, comets (BS Ch. 11).

---

## 3. Transit and Dasha-Equivalent Techniques

| Technique | How it is used | Status |
|---|---|---|
| **Eclipses** | Locate sign and nakshatra (BS 5.35–42 + Ch. 14 for regions). Overlay on the foundation chart: an eclipse within a few degrees of the lagna, Moon, Sun or 10th lord is the activation; the house it falls in names the domain. BS 5.63: effects may recur at 6-month multiples. Solar + lunar pairs per BS 5.97–98. The "few degrees" orb is a working rule. | [classical] sign/month/region rules; orb [exploratory] |
| **Graha-yuddha** | Two true planets (not Sun, Moon or nodes) within 1°; BS Ch. 17 gives winner, loser and results. | [classical] |
| **Retrograde stations** | Saturn/Jupiter stationing on a sensitive degree of the foundation chart; a slow body that stations sits on the point for weeks. | [synthesis] |
| **Jupiter–Saturn conjunction** | Cast for the capital; house and nakshatra of the conjunction in the foundation chart. **Sidereal and tropical framings disagree** (§6 row 8): the Western element "mutation" does not hold sidereally. | [tradition, non-Indian] |
| **Jupiter samvatsara** | Name of the year and its BS Ch. 8 result. | [classical] |
| **Cabinet of the year** | Raja/Mantri/Sasyesha etc. per Narada Samhita; BS Ch. 19 for the year-lord's result. | [classical] |
| **Mesha Sankranti chart** | Annual chart for the capital: lagna, 10th, Moon and their lords for the year. | [tradition] |
| **Lunation charts** | Amavasya chart before the month, cast for the capital; Purnima for the fortnight. Angular malefics and the Moon's condition are read. | [tradition] |
| **National Sade Sati** | Saturn through the 12th/1st/2nd from the foundation-chart Moon; Ashtama Shani = Saturn in the 8th from it. Method as in instructions §6. | [synthesis]; no classical text applies Sade Sati to a nation |
| **National Vimshottari** | From the foundation-chart Moon's nakshatra, as for a native. | [synthesis] |
| **National Varshaphala** | Tajika annual return of the foundation Sun. | [synthesis] |
| **Ashtakavarga** | SAV of the foundation chart grades transit houses (BPHS Ashtakavarga chapters, by analogy). | [synthesis] |
| **Kota chakra** | 28 nakshatras (with Abhijit) laid in four concentric squares (outer to inner: bahya, prakara, durga, stambha) from the foundation/janma nakshatra. Kota-swami (lord of the Moon's sign) and kota-pala (guardian by pada) are judged; malefics moving inward (especially retrograde) = pressure on the "fort"; benefics inside = protection. | Agni Purana Ch. 128 [classical, existence]; mechanics [tradition, unverified] |

---

## 4. Foundation Charts on Record

All positions are **own computation**: Swiss Ephemeris (Moshier), Lahiri, true node, run 2026-10-09.

### 4.1 India: 15-Aug-1947 00:00 IST, New Delhi (28.61N, 77.21E)
The chart in universal use for the Dominion of India (independence took legal effect at midnight).
- **Lagna Taurus 7°44'.** Rahu Taurus 5°44' (1st), Mars Gemini 7°28' (2nd).
- **Cancer (3rd): Sun 27°59', Moon 3°59' (Pushya), Mercury 13°40', Venus 22°34', Saturn 20°28'.**
- Jupiter Libra 25°53' (6th), Ketu Scorpio (7th).
- Moon in Pushya (Saturn) → Vimshottari opens in **Saturn MD** (balance ~18 yr of 19).
  MDs: Saturn → Sep-1965 · Mercury → Sep-1982 · Ketu → Sep-1989 · Venus → Sep-2009 · Sun → Sep-2015
  · Moon → Sep-2025 · **Mars Sep-2025 → Sep-2032** · Rahu → 2050 (365.25-day year).
- **Born under Sade Sati** (Saturn in Cancer, on the Moon sign, since Jun-1946).
  National Sade Sati cycles (Moon Cancer): Saturn into Gemini Jun-1973 → leaves Leo Nov-1979 (brief Leo
  return Mar–Jul 1980) · Gemini Jul-2002 → leaves Leo Sep-2009 · next: Gemini May-2032 → leaves Leo
  Oct-2038 (Leo return Apr–Jul 2039). Ashtama Shani (Aquarius): 1964–66, 1993–96, 2022–25.
- No lagna variants in common use. Mean node puts Rahu at Taurus 5°04': same house.

### 4.2 USA: 04-Jul-1776, Philadelphia (39.95N, 75.17W, LMT = UT−5h01m)
**Chart on record (Sai's decision 2026-10-14): Sibly 17:10 LMT.** Founding event = adoption of the
Declaration of Independence, 04-Jul-1776, Philadelphia. One alternative subject is registered: the
Federal Reserve Act chart, §4.2b. Ruling by jyotish-agent 2026-10-14, on text grounds, before any
data is joined. Own computation: Swiss Ephemeris (Moshier) via `scripts/jyotish_core.py`, Lahiri,
**true node**, LMT from 75.17W (UT−5h00m41s; the rounded UT−5h01m gives lagna 21°41', the v1 figure).

**Ruling.** Sibly 17:10 is a **defensible convention chart, not a recorded instant.** It is used
because (a) it is the oldest published USA figure: Ebenezer Sibly, *A New and Complete Illustration of
the Celestial Science of Astrology*, published 1787 per secondary sources; one secondary source cites
it as Fig. 53 after p. 1055 of the 1826 posthumous edition; the two dates are not reconciled
[tradition, secondary: theastrologypodcast.com "What is the Birth Chart of the United States?";
Anthony Louis blog "The Sibly Chart of the USA"]; and (b) 17:10 falls inside Congress's day session of
04-Jul-1776, when the Declaration was adopted [the Journals of the Continental Congress, vol. 5, record
the adoption on 4 July but **no hour**; "afternoon" is the National Archives' account as reported
second-hand; Jefferson's and Adams's recollections put the floor action late morning. Primary entry
not read; hour UNVERIFIED]. Against it: Sibly gives no source for the time, and his own figure is
argued to be cast for London ~22:10 (≈17:10 Philadelphia, same UT) or derived from the Aries/Cancer
ingress charts [tradition, secondary, contested]. **Consequence:** only what holds across the whole
day session (table below) is the USA chart's robust content; every statement that depends on the
Scorpio lagna or the exact dasha clock stays **[exploratory]** and names "Sibly 17:10".

**Classical position on a nation's "birth".** No primary passage was found that prescribes a
foundation-moment chart for a land. Brihat Samhita judges lands through the planetary courses and
Kurma Vibhaga (Ch. 14), not through a national nativity; the foundation-moment chart is modern Indian
practice (the India 1947 midnight chart, Raman-era usage) extending Hora to an entity
[synthesis; §2.1; primary source UNVERIFIED].

**Exclusion rule: the night variants (02:14, 03:03 LMT, and any time outside the day session) are
excluded as the chart of record.** Congress was not sitting at those hours, and the sources trace
them to symbolic construction, not to any record of the act: the Gemini-rising chart to Luke
Broughton (1861; the Uranus degree taken as rising) and to the Philadelphia Cancer-ingress horizon of
20-Jun-1776; Evangeline Adams's 03:03 to the angles of the 14-Aug-1776 partial solar eclipse
[tradition, secondary: Anthony Louis blog "Mystery Solved: the USA Gemini Rising Chart"; The
Astrology Podcast]. Their standing rests on symbolic fit and on fit to later events: **outcome-chosen,
therefore excluded under the firewall** (§2.2: never pick the variant that "works" after the fact).
The 02:14 chart is cast below **only** as the labelled exploratory comparison that §2.2 requires.

**Sibly 17:10 LMT cast (UT 22:10:40; ayanamsa 20°44').**
- **Lagna Scorpio 21°37' (Jyeshtha 2).** 8.4° (~40 min) before Sagittarius; Scorpio rises ~15:23-17:49 LMT.

| Graha | Sign | Deg | Nakshatra-pada | House | Flags |
|---|---|---|---|---|---|
| Sun | Gemini | 22°35' | Punarvasu 1 | 8 | |
| Moon | Aquarius | 6°26' | Dhanishta 4 | 4 | 0.23° (~22 min) before Shatabhisha |
| Mars | Gemini | 0°39' | Mrigashira 3 | 8 | 0.6° into the sign |
| Mercury | Cancer | 3°28' | Pushya 1 | 9 | **retrograde, combust** (10.9° from Sun; retro orb 12°) |
| Jupiter | Gemini | 15°12' | Ardra 3 | 8 | **combust** (7.4°) |
| Venus | Gemini | 12°22' | Ardra 2 | 8 | not combust: 10.2° from Sun vs 10° orb (edge) |
| Saturn | Virgo | 24°04' | Chitra 1 | 11 | |
| Rahu (true) | Cancer | 15°52' | Pushya 4 | 9 | true node momentarily direct at this instant; nodes read as retrograde by convention |
| Ketu (true) | Capricorn | 15°52' | Shravana 2 | 3 | |

Mean node: Rahu Cancer 16°51' **Ashlesha 1**: same sign and house, different nakshatra. Use the true node.
- **Moon Dhanishta 4 (Mars) → Vimshottari opens in Mars MD, balance 0.12 yr (~44 days).**
  MDs (365.25-day year), start dates: Mars at founding · Rahu 17-Aug-1776 · Jupiter Aug-1794 ·
  Saturn Aug-1810 · Mercury Aug-1829 · Ketu Aug-1846 · Venus Aug-1853 · Sun Aug-1873 · Moon Aug-1879
  · Mars Aug-1889 · Rahu Aug-1896 · Jupiter Aug-1914 · Saturn Aug-1930 · Mercury Aug-1949 · Ketu Aug-1966
  · Venus Aug-1973 · Sun Aug-1993 · Moon Aug-1999 · Mars Aug-2009 · **Rahu Aug-2016 → Aug-2034** ·
  Jupiter Aug-2034 → Aug-2050.
  Sagent's provisional figures (Scorpio 21°37', Moon Aquarius 6°26' Dhanishta 4, Mars balance ~0.1 yr,
  Rahu MD from ~Aug-1776) are **verified**.
- **Sign-edge caution.** The Moon leaves Dhanishta at **17:32 LMT**. From then the Moon is in
  Shatabhisha, the dasha opens in Rahu and the whole sequence changes. The Sibly dasha therefore
  depends on the time being right to within ~22 minutes. Every Sibly dasha statement is [exploratory].

**Time-robustness across the day session (06:28-17:32 LMT).** The window is bounded by the Moon's
own boundaries: Capricorn→Aquarius at 06:28 LMT, Dhanishta→Shatabhisha at 17:32 LMT.

| Fact | 06:28-17:32 LMT | Note |
|---|---|---|
| Moon sign Aquarius, nakshatra Dhanishta (pada 3 to 12:01, pada 4 after) | **holds** | national Sade Sati is anchored on Aquarius |
| Dasha order (Mars → Rahu → Jupiter → ...) | **holds** | |
| Sun, Mars, Jupiter, Venus in Gemini; Mercury R in Cancer; Saturn in Virgo; Rahu Cancer / Ketu Capricorn | **holds** (all day, 00:00-23:59) | Mercury retrograde + combust and Jupiter combust also hold all day |
| Graha nakshatras other than the Moon | **holds** in the window | Mercury moves back into Punarvasu only near midnight 4/5 July |
| Lagna | **does not hold** | Cancer 14° (06:30) → Leo (~07:50) → Virgo (~10:21) → Libra (~12:50) → Scorpio (~15:23) → Sibly Scorpio 21°37' |
| Dasha clock | **does not hold** | opening Mars balance runs from ~3.5 yr (06:28) to 0.12 yr (17:10): every MD boundary shifts by up to **~3.4 yr**, about 3.8 months per hour of birth time (e.g. Rahu MD from Aug-2016 under Sibly vs ~Dec-2019 at 06:30) |
| House position of every graha | **does not hold** | follows the lagna |

Robust core for any USA statement: Moon Aquarius/Dhanishta, Mars-first dasha order, every graha's sign.
Lagna, houses and dated dasha boundaries are Sibly-specific → [exploratory].

**Exploratory comparison (EXCLUDED as chart of record): Gemini-rising 02:14 LMT** (UT 07:14:40).
Lagna **Taurus 16°47'** (Rohini 3; the v1 table gave 16°53' with the rounded offset). Moon **Capricorn
27°26' Dhanishta 2** (9th); Sun Gemini 22°00', Mars Gemini 0°13', Jupiter Gemini 15°04' (combust),
Venus Gemini 11°37' (all 2nd); Mercury R Cancer 3°44' Pushya 1, combust, and Rahu (true) Cancer 15°51'
(3rd); Saturn Virgo 24°03' (5th); Ketu Capricorn (9th). Mars MD balance 4.84 yr; MD starts: Rahu
May-1781 · Jupiter May-1799 · ... · Mars May-2014 · **Rahu May-2021 → May-2039** · Jupiter May-2039.
Adams 03:03 = Taurus 29°42', 0.3° from Gemini: unstable. Label any reading from these
"[exploratory] Gemini-rising 02:14" and never cite it as the USA chart.

**Historical (v1, 2026-10-09) variant table, kept for reference.** The dispute is over the time,
not the date (a further argument holds that the signing was 02-Aug-1776). Tropical labels are how
Western sources name them.

| Variant | Time (LMT) | Tropical asc (source label) | **Sidereal lagna (Lahiri)** |
|---|---|---|---|
| Sibly (Ebenezer Sibly, 18th c.; most used in the West) | 17:10 | Sagittarius ~12° | **Scorpio 21°41'** |
| Gemini rising (common version) | ~02:14 | Gemini ~7° | **Taurus 16°53'** |
| Evangeline Adams (argued to be a symbolic, eclipse-based chart) | 03:03 | Gemini ~20° | **Taurus 29°47', at the sign edge: unstable** |
| "Scorpio rising" (from the $100-bill clock, read as 14:22; also read as 16:10) | 14:22 / 16:10 | Scorpio | **Libra 18°07' / Scorpio 9°29'** |
| Libra-rising proposal (2026; argues Sibly's chart was a London ingress) | not fixed | Libra | not computed; claim unverified |

v1 time-robust features (all variants): Sun Gemini 22°, Jupiter Gemini 15°, Venus Gemini 12°, Mars
Gemini 0–1°, Mercury Cancer 3–4° retrograde, Saturn Virgo 24°, Rahu Cancer 16°. Moon is Aquarius
in the afternoon variants and **Capricorn 27–28° in the night variants, Dhanishta in every
variant** → Vimshottari opens in Mars MD in all of them, with different balances. (v1 text "No
agreed chart" is superseded by the ruling above, 2026-10-14.)

### 4.2b Alternative subject: Federal Reserve Act, 23-Dec-1913, Washington DC (38.89N, 77.04W, EST = UT−5)
Registered by Sai 2026-10-14 as the ONE alternative subject. **Defensible as the chart of an
institution, not of the nation:** the act of legal existence is the President's signature (§2.1,
item 1). Statements from it describe the Federal Reserve as an entity and are [synthesis] at best.

**Signing hour: 18:02 EST, ACCEPTED as the working convention by Sai 2026-10-14 (secondary sources only; primary unverified).** A 1913 *New York Times* report, quoted on a third-party
timeline (time.graphics), gives **6:02 p.m.**; the U.S. Senate historical office ("Senate Passes the
Federal Reserve Act", senate.gov) gives **6:00 p.m.** Both are secondary; the original newspaper page
was not checked [primary UNVERIFIED]. Civil time assumed = Eastern Standard (75°W); DC local mean
time (UT−5h08m) would move the lagna to Gemini 27°07'.

**Cast, 18:02 EST (UT 23:02).** Lagna **Gemini 25°25'** (Punarvasu 2; 4.6° = ~22 min before Cancer;
Gemini holds until ~18:24 EST; 18:00 gives Gemini 25°00').

| Graha | Sign | Deg | Nakshatra-pada | House | Flags |
|---|---|---|---|---|---|
| Sun | Sagittarius | 8°53' | Mula 3 | 7 | |
| Moon | Libra | 21°52' | Vishakha 1 | 5 | |
| Mars | Gemini | 26°53' | Punarvasu 3 | 1 | **retrograde** |
| Mercury | Scorpio | 21°18' | Jyeshtha 2 | 6 | |
| Jupiter | Capricorn | 0°40' | Uttara Ashadha 2 | 8 | debilitation sign; 0.7° into it |
| Venus | Scorpio | 26°57' | Jyeshtha 4 | 6 | |
| Saturn | Taurus | 20°41' | Rohini 4 | 12 | **retrograde** |
| Rahu (true) | Aquarius | 25°47' | Purva Bhadrapada 2 | 9 | mean node 26°10', same nakshatra |
| Ketu (true) | Leo | 25°47' | Purva Phalguni 4 | 3 | |

No graha combust. Moon Vishakha (Jupiter) → **Jupiter MD, balance 13.77 yr.** MD starts: Saturn
Sep-1927 · Mercury Sep-1946 · Ketu Sep-1963 · Venus Sep-1970 · Sun Sep-1990 · Moon Sep-1996 · Mars
Sep-2006 · **Rahu Sep-2013 → Sep-2031** · Jupiter Sep-2031 → Sep-2047.

**Fed time-robustness (Moon rule).** All day 23-Dec-1913 (00:00-23:59 EST): Moon **Libra** and
every other graha's sign and nakshatra hold. The Moon's nakshatra does **not**: Swati (Rahu MD first)
before **14:51 EST**, Vishakha (Jupiter MD first) after. Both reported hours (18:00, 18:02) fall
after 14:51, so Moon Vishakha 1 and the Jupiter-first dasha order hold for either; the dasha clock
moves ~8.5 months per hour. The lagna depends on the hour (Gemini only 16:08-18:24 EST) → [exploratory]. If the hour is ever
rejected, fall back to date-only: Moon Libra, graha signs, and no dasha.

### 4.3 Market entities (astro-market Phase 0 register, 2026-10-09)

Machine-readable register: `C:\Users\ssair\astro-market\foundation_register.json` (28 entries; owner
jyotish-agent). This section records the doctrine and the lineage findings. It records **dates and
places only**; no chart is read here, and no statement about price is made or implied (§5 firewall).

**Doctrine.**
- **First public trade = birth; trust creation / initial deposit = conception; listing approval and SEC
  orders start nothing.** [synthesis] The analogy is Brihat Jataka ch. 4 (conception distinguished from
  birth) and the shop-opening (vyapara-arambha) muhurta, where the commencement of trade is the moment
  that counts [tradition]. An ETF is not a native and an index is not a nation; every market-entity chart
  is [synthesis] at best.
- **Time.** The stored time is the 09:30 session open, not a recorded first print. Each Tier A lagna's
  distance from a sign boundary must be recorded (a 10-minute delay moves the lagna about 2.5°).
  **Rectification ban:** no foundation time is adjusted to fit market history.
- **Place of the act.** The 1993–99 listings: American Stock Exchange, 86 Trinity Place (40.7081N
  74.0124W). XLRE and XLC: NYSE Arca, which has no floor; its corporate seat (11 Wall Street) is used
  [synthesis].
- **Relisting / ticker-change rule** [synthesis]. Renames, ticker changes (QQQ → QQQQ 2004 → QQQ 2011),
  exchange moves (AMEX → NYSE Arca or Nasdaq), sponsor changes and constituent changes do **not** create a
  new chart. A name change is a naming, not a birth. Replacing the defining mandate (the index the fund
  exists to track) breaks the **sector-level** lineage: the legal fund keeps its 1998 chart, but that
  chart is not the chart of the new sector vehicle. A carve-out produces a child (its own first-trade
  chart), not a rebirth of the parent.
- **Tier B (index launches; date only).** Only Moon-based techniques apply: Moon sign as lagna
  (Chandra lagna) [classical, BPHS]; planets by sign and nakshatra; transits counted from the Moon;
  eclipse contacts with natal planets. Not available: SAV (the lagna is a contributor) and Vimshottari
  (the balance needs the Moon's exact longitude). **Rule:** the entry is usable only if the Moon's
  sidereal sign **and** nakshatra (Lahiri) hold from 00:00 to 23:59 New York local time; otherwise record
  both and mark it UNSTABLE. The same rule governs every date-only `inception` variant.
- **Tier C (prose only, not in the register):** NYSE 1792-05-17 (Buttonwood; date confirmed, no
  pre-2003 rectified time exists, weak link to ETFs); USA 1776 (§4.2; disputed time).

**Register summary** (dates confirmed from the issuers' own SEC filings unless noted):

| Subject | First trade (birth) | Inception (conception) | Place | Notes |
|---|---|---|---|---|
| SPY | 1993-01-29 09:30 | 1993-01-22 (Initial Date of Deposit) | AMEX | 09:30 open in Jan-1993 **probable, unconfirmed** |
| QQQ | 1999-03-10 09:30 | 1999-03-04 (deposit; first issuance 03-05) | AMEX | 03-04 is WRONG as a first-trade date |
| Nine sector SPDRs | 1998-12-22 09:30 | 1998-12-16 | AMEX | 09:30 open confirmed by the Trust's 1998-12-21 prospectus |
| XLRE | 2015-10-08 09:30 | 2015-10-07 | NYSE Arca | early-session first print possible |
| XLC | 2018-06-19 09:30 | 2018-06-18 | NYSE Arca | **resolved:** 06-18 = series created, 06-19 = first listing (Trust N-CSR FY2018) |
| S&P 500 (Tier B) | 1957-03-04 index launch | — | New York | Moon rule |
| Nasdaq-100 (Tier B) | 1985-01-31 index launch | — | place unverified, NY tz | Moon rule |

**Lineage of the 1998 series** (Select Sector SPDR Trust, CIK 1064641: 497 of 1998-12-21; supplement of
2002-04-15; 485BPOS of 2002-06-21; supplements of 2016-09-02 and 2018-06-19). The 1998 tickers are
today's tickers; the **names and mandates** are not. Index changes took effect at the open of 2002-06-24.

| Ticker | 1998 series | Today | 1998 chart inherited | Reason |
|---|---|---|---|---|
| XLB | Basic Industries | Materials | YES | rename only; same industries continued |
| XLV | **Consumer Services** | Health Care | **NO** | mandate replaced 2002 (media, foods, lodging, gaming → health care) |
| XLP | Consumer Staples | Consumer Staples | YES | pharma removed 2002 (flag) |
| XLY | **Cyclical/Transportation** | Consumer Discretionary | **UNCONFIRMED** | partial overlap (retail, autos kept; transports out; media, hotels in); also lost names to XLC 2018 |
| XLE | Energy | Energy | YES | no change found in the filings read |
| XLF | Financial | Financial | YES | real estate carved out to XLRE after close 2016-09-16 (child, not rebirth) |
| XLI | Industrial | Industrial | YES | transports added 2002 (flag) |
| XLK | Technology | Technology | YES | telecom in 2002, out to XLC 2018 (flags) |
| XLU | Utilities | Utilities | YES | telecom out 2002 (flag) |

XLRE and XLC are born entities with their own charts. Their holdings arrived later by carve-out
(XLRE Sept 2016 from XLF; XLC 2018-09-21 from XLK/XLY). That is growth after birth, not inheritance.

---

## 5. Method Checklist (run in order; every box before delivery)

**Scope (Lesson 39, instructions §7A):**
□ The question is about a collective subject (nation, region, weather, a class of events). A
  question about a named living person goes to the natal workflow with their own birth data, or is declined.
□ **No trading, investment, financial, political, military, travel or personal advice.** Markets
  may be described as a mundane subject (what the chart shows for the 2nd/11th/Mercury), never as a
  call to act or a price direction, and never routed to trading or research work (firewall).
□ **No statement on the death, health or removal of a named living person.**
□ STRANGER and PROPER-NOUN tests (instructions §7A) on every sentence. Names of parties, leaders
  and companies appear only as historical evidence being classified.

**Data (instructions §7B):**
□ Chart named with date, time, place, ayanamsa and node type. Disputed time → every variant run (§2.2).
□ Missing foundation data → ask; never invent a time. Headless → stop and report what is missing.

**Analysis:**
□ Each technique named with its status tag and source (§1, §3).
□ Region/house attribution stated from the chart (BS 5.35–42, Ch. 14; §2.3), not from the news.
□ At least two independent techniques agree (e.g., eclipse overlay + dasha, or Sankranti chart +
  Sade Sati). A single-technique finding is [exploratory].

**Forward windows (Lesson 38), mandatory:**
□ Name the comparable past configurations (same eclipse axis, same JS-conjunction sign, same Sade
  Sati phase, same dasha lord) from §6 or new computation, and what happened.
□ **Lead with the precedent that contradicts the forecast.** §6 rows 2 and 8 are the standing
  examples: widely predicted catastrophes that did not occur.
□ Mark each analogue **doc-cited** (event and configuration documented in a named source) or
  **own computation**. Mundane work has no "native-confirmed" tier; when Sai confirms a historical
  date it is recorded as for natal charts.
□ State the base rate: eclipses 2–5 a year; Saturn back in a sign every ~29.5 yr; JS conjunction
  every ~19.9 yr. A configuration that recurs often explains little on its own.
□ State what the chart shows, then STOP. No "therefore one should".

**Close:** upayas only if asked, in classical form, each naming its graha (e.g., Shani shanti for
an afflicted national Saturn). Log the run; add any resolved mundane statement to §6.

---

## 6. Historical Analogue Table

Positions: own computation (Lahiri, true node), 2026-10-09. **doc-cited** = the event and the
configuration's notoriety are documented in a named source; **own** = configuration and dasha
computed here, not taken from a published reading. Event dates are historical fact; the
dasha/transit links are interpretation.

| # | Date | Event | Configuration at the time | Tag |
|---|---|---|---|---|
| 1 | 15-Aug-1947 | Independence and Partition of India | India chart itself: born at the Sade Sati peak (Saturn on the Moon sign Cancer), five planets in the 3rd (neighbours, borders), Rahu on the lagna. | own (chart widely published) |
| 2 | 4–5 Feb-1962 | **Ashtagraha**: 8 bodies (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Ketu) in sidereal Capricorn with a total solar eclipse; ~11½ months after the Feb-1961 JS conjunction in Capricorn 2° | **CONTRADICTING PRECEDENT:** a widely spread end-of-the-world prediction (end time quoted as 17:38 on 5-Feb) did not occur; mass prayer meetings; the Prime Minister called the panic absurd. | doc-cited (The Wire; Madras Courier); configuration own |
| 3 | 20-Oct-1962 | Sino-Indian war begins | India chart Saturn MD / **Rahu AD** (Apr-1960 → Feb-1963; Rahu natal on the lagna); Saturn transiting Capricorn, the 9th from Taurus and the sign of the Feb eclipse; ~8½ months after the eclipse (between BS 5.63's 6- and 12-month marks). | own |
| 4 | 25-Jun-1975 | The Emergency declared in India | India chart Mercury MD / Rahu AD (from Mar-1975); Saturn Gemini 26° = Sade Sati rising phase, entering Cancer (over the Moon) a month later. | own |
| 5 | 31-Oct-1984 | Assassination of India's Prime Minister | India chart Ketu MD / Moon AD (from Aug-1984); Saturn Libra 24° (6th from lagna, 4th from Moon: kantaka). | own |
| 6 | 26-Dec-2004 | Indian Ocean earthquake and tsunami | Saturn retrograde Cancer 1°28', 2½° from India's natal Moon (Sade Sati peak, cycle 3); India chart Venus MD / Saturn AD (Jul-2002 → Sep-2005). | own |
| 7 | 26-Dec-2019 → 11-Mar-2020 | Annular solar eclipse in sidereal Sagittarius (Mula) with six bodies (Sun, Moon, Mercury, Jupiter, Saturn, Ketu); WHO declares a pandemic 11-Mar-2020 | Eclipse in the 8th from India's Taurus lagna; India chart Moon MD / **Saturn AD from Dec-2019**; Saturn entered Capricorn 25-Jan-2020. The eclipse-pandemic link circulated widely in Vedic commentary; no specific published author verified. | own (popular attribution unverified) |
| 8 | 31-Dec-1980 → Jul-1981 | Triple Jupiter–Saturn conjunction, sidereal Virgo ~16° (Hasta); tropical Libra, the Western "early air mutation" | **CONTRADICTING PRECEDENT (Western lore):** the "zero-year" presidential-death pattern tied to JS conjunctions; the US President elected in 1980 was shot on 30-Mar-1981 and survived. Also shows the **zodiac disagreement**: sidereal JS conjunctions run 1940–41 Aries (fire) · 1961 Capricorn · 1980–81 Virgo · 2000 Aries 28°52' (fire) · 2020 Capricorn 6°20' · 2040 Virgo 23°34', with no clean element series, unlike the tropical sequence. | doc-cited as Western lore; positions own |
| 9 | 11-Sep-2001 | Attacks on New York and Washington | Saturn Taurus 21°, Rahu Gemini 9°, Jupiter Gemini 18°. **Chart choice changes the reading:** Gemini-rising variant (sidereal Taurus lagna) → Saturn on the lagna; Sibly (sidereal Scorpio lagna) → Saturn in the 7th, Rahu + Jupiter in the 8th. Robust across variants: Rahu and Jupiter transiting the natal Gemini Sun–Jupiter–Venus group. | own |
| 10 | 21-Dec-2020 | Jupiter–Saturn conjunction, sidereal Capricorn 6°20' (Uttarashadha) | Capricorn = 9th from India's lagna, the same sign as the 1961 conjunction and the 1962 ashtagraha (rows 2–3). Recorded as the anchor for the current ~20-year cycle; no outcome attributed. | own |

**How to use this table:** match a forward configuration to the nearest rows by technique, read
the contradicting rows first, and say plainly when the matching rows disagree. Add a row whenever
a mundane statement resolves (with the resolution date and whether Sai confirmed it).

---

## 7. Known Gaps (v1, refreshed 2026-10-14)

- B.V. Raman's *Mundane Astrology* and a full Brihat Samhita PDF are not in `../texts/`; the BS
  chapter/verse numbers above come from the Chidambaram Iyer translation on wisdomlib.
- Kota chakra mechanics and the Ardra-pravesha rain rule are unverified against primary texts.
- USA chart: RESOLVED by convention 2026-10-14 — Sibly 17:10 LMT is the chart on record (§4.2), with
  the Fed 1913 chart at 18:02 EST as the one alternative (§4.2b). Neither hour is a primary record;
  no classical passage on a nation's birth chart was found, so the convention itself is [synthesis].
  Still open: the Journals of Congress hour (none exists) and the NYT 24-Dec-1913 page for the Fed hour.
- Mundane event finders (eclipse, Sankranti, lunation, ingress, Jupiter-Saturn) now live in
  `scripts/jyotish_core.py` and the `mundane` subcommand of `compute_chart.py` (tech-agent build run 1,
  2026-10-09). The foundation-chart overlay for mundane events is NOT built.
