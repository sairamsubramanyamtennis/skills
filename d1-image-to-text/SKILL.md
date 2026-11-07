---
name: d1-image-to-text
description: "Convert a South Indian D1 (Rashi) chart IMAGE into the plain-text birth-chart format used to feed jyotish-reader. Reads the chart picture, decodes each sign/planet/degree from the fixed South-Indian square grid, asks the user for the native's name and full birth data, and emits the ready-to-paste text block ('For this date of birth ... the following is the D1 chart ... Native is a ...'). Triggers ONLY when explicitly invoked: 'convert this D1 image', 'read this D1 chart image', 'D1 image to text', 'chart image to jyotish format', 'convert rashi chart picture', 'turn this chart image into text', or the user shares a Rashi/D1 chart image and asks to convert/transcribe it. Do NOT trigger for running an actual reading (that is jyotish-reader) or for non-chart images."
---

# D1 Chart Image → Text

Convert a **South Indian D1 (Rashi) chart image** into the exact plain-text format the user
feeds to the `jyotish-reader` skill. This skill only **transcribes** the image; it does not
interpret the chart.

## When to invoke

ONLY when explicitly asked to convert / transcribe / read a D1 chart **image** into text.
Do NOT invoke to perform an astrology reading (use `jyotish-reader` for that).

## Inputs

1. **The chart image** — a file path or attached image of a South Indian Rashi (D1) chart.
   Example reference image: `C:\Users\ssair\jyotish-readings\eample-d1.jpg`.
2. **Native's name** — always ask.
3. **Full birth data** — Date, Time, Place (City, State, Country), Gender. These are **NOT in
   the image** and must be collected from the user. Ask for any that are missing.

## Workflow

1. **Read the image** with the Read tool.
2. **Decode the grid** using the fixed South-Indian layout below. For every occupied cell,
   record: sign (from the cell's fixed position), each planet's 2-letter code, and its
   degrees°minutes′.
3. **Locate the Ascendant** by finding the `As` marker and reading the sign of **the cell it
   sits in**. ⚠️ Never infer the Ascendant sign from a planet — read its own cell.
4. **Ask the user** for the native's name and any missing birth data (date, time, place,
   gender). Use one clear prompt.
5. **Emit the text block** in the exact output format below.
6. **Self-check** against the validation checklist, then present the result. Offer to hand it
   straight to `jyotish-reader`.

## Fixed South-Indian sign layout (4×4 grid)

Signs are always in these fixed cells (row, col), 0-indexed from the top-left. Planets move;
the signs never do. The center 2×2 is blank.

```
(0,0) Pisces     (0,1) Aries      (0,2) Taurus     (0,3) Gemini
(1,0) Aquarius   [   center   ]   [   center   ]   (1,3) Cancer
(2,0) Capricorn  [   center   ]   [   center   ]   (2,3) Leo
(3,0) Sagittarius(3,1) Scorpio    (3,2) Libra      (3,3) Virgo
```

Reading the border clockwise from top-left: Pisces → Aries → Taurus → Gemini → Cancer → Leo
→ Virgo → Libra → Scorpio → Sagittarius → Capricorn → Aquarius → (back to Pisces).

## Planet / body codes

| Code | Body      | | Code | Body       |
|------|-----------|-|------|------------|
| `Su` | Sun       | | `Ve` | Venus      |
| `Mo` | Moon      | | `Sa` | Saturn     |
| `Ma` | Mars      | | `Ra` | Rahu       |
| `Me` | Mercury   | | `Ke` | Ketu       |
| `Jp` / `Ju` | Jupiter | | `As` | Ascendant (Lagna) |

If upagrahas (`Gu` Gulika, `Md`/`Ma` Mandi, etc.) or outer planets appear, ignore them unless
the user asks to include them — the target format uses the 9 grahas + Ascendant only.

## Reading each cell

- Degrees look like `17°31'` → **17 degrees and 31 minutes**. `0°3'` → 0 deg 3 mins.
- The tiny **superscript letters** next to a body (e.g. `Mu`, `Kr`, `Ci`, `Sr`, `UA`) are
  **nakshatra tags** — IGNORE them; the output format does not use nakshatras.
- **Underlines / an `R`** usually mark retrograde. The target format does not include
  retrograde, so ignore unless the user asks. (Rahu/Ketu are always retrograde.)
- One cell can hold several planets (list them all).

## Output format

Order the occupied signs **zodiacally, starting from the Ascendant's sign**, and list the
Ascendant first. Omit empty signs. Name the Ascendant's sign explicitly.

```
For this date of birth <Month DD YYYY>, <H:MM AM/PM>, <City, State, Country>, the following is the D1 chart
Ascendant is <Sign> at <D> degrees and <M> minutes; <Sign> has <Planet> <D> deg and <M> mins[, <Planet> <D> deg and <M> mins ...]; <Sign> has <Planet> <D> deg and <M> mins; ...
Native is a <Male/Female>.
```

Planet names spelled in full: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu.

## Self-validation checklist

- [ ] Exactly one `As` (Ascendant) located, and its sign read from its **own** cell.
- [ ] All 9 grahas accounted for (Su, Mo, Ma, Me, Jp, Ve, Sa, Ra, Ke) — flag any missing.
- [ ] Rahu and Ketu are exactly 180° apart (opposite signs, same degree/minute). If not,
      re-check the reading.
- [ ] Every degree is 0–29° and every minute is 0–59′.
- [ ] Name, date, time, place, gender all present in the output header/footer.

## Worked reference example (validates the decoder)

Image `eample-d1.jpg` decodes as:

| Cell | Sign | Contents |
|------|------|----------|
| (0,1) | Aries | Ma 0°3′ |
| (0,2) | Taurus | Sa 6°6′ |
| (1,0) | Aquarius | Ve 24°56′ |
| (1,3) | Cancer | Ke 11°47′ |
| (2,0) | Capricorn | Su 17°31′, Ra 11°47′, Me 6°10′ |
| (2,3) | Leo | Mo 3°2′ |
| (3,0) | Sagittarius | Jp 5°22′ |
| (3,2) | **Libra** | **As 5°56′** ← Ascendant |

Correct output (birth data supplied by the user; here Jan 31 1972, 11:50 PM, Solapur,
Maharashtra, India, Male):

```
For this date of birth January 31 1972, 11:50 PM, Solapur, Maharashtra, India, the following is the D1 chart
Ascendant is Libra at 5 degrees and 56 minutes; Sagittarius has Jupiter 5 deg and 22 mins; Capricorn has Sun 17 deg and 31 mins, Rahu 11 deg and 47 mins, Mercury 6 deg and 10 mins; Aquarius has Venus 24 deg and 56 mins; Aries has Mars 0 deg and 3 mins; Taurus has Saturn 6 deg and 6 mins; Cancer has Ketu 11 deg and 47 mins; Leo has Moon 3 deg and 2 mins.
Native is a Male.
```

Note: Rahu 11°47′ Capricorn and Ketu 11°47′ Cancer are exactly opposite ✓ — a good sanity check.

---

## Telemetry (standing requirement — all skills)

Log this run **once, at the very end**, whether it went well or not (Bash tool; forward slashes):

```bash
python C:/Users/ssair/.claude/telemetry/telemetry.py log --skill d1-image-to-text \
  --outcome delivered|partial|blocked|corrected|routed \
  --asked    "what he actually wanted, one line" \
  --produced "what he got, one line" \
  [--friction "what slowed it down or went wrong"] [--routed-to <skill>] [--tags a,b]
```

* `corrected` = Sai had to push back before it was right. **Log it.** A telemetry file that is all
  `delivered` is worthless for skill health — the corrections and blocks are the whole point.
* One record per run, not per step. Silent side effect: never announce it, never ask permission for
  it, never let it delay or clutter the answer.
* Paraphrase in `--asked`; never log credentials, birth data, account numbers or verbatim personal
  detail. If the call fails, drop it and move on.

Full contract: `C:/Users/ssair/.claude/telemetry/TELEMETRY.md` · read it back in the Recap app's
Telemetry page or via `telemetry.py stats --days 30`.
