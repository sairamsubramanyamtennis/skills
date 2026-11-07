#!/usr/bin/env python3
"""
page_check.py - inspect a built resume the way a reader will actually see it.

`build_resume.py` can only estimate length from text metrics. When Microsoft
Word is installed (checked via the Word.Application COM object) this script
gets the REAL numbers from Word's layout engine, and can export a PDF and
render each page to PNG so the rendered appearance can be inspected rather
than assumed - SKILL.md section 21.

    python page_check.py resume.docx                  # real page/word counts
    python page_check.py resume.docx --pdf out.pdf    # also export a PDF
    python page_check.py resume.docx --png outdir/    # render pages to PNG
    python page_check.py SS.doc --docx new.docx       # convert legacy .doc

Also reports, per page, how full the last page is - the "page that is 12% full"
problem that makes a resume look padded.

Requires: pywin32 and Microsoft Word. Fails with a clear message otherwise.
"""

import argparse
import os
import sys
from pathlib import Path

WD_STAT_WORDS, WD_STAT_PAGES, WD_STAT_LINES = 0, 2, 1
WD_FORMAT_PDF = 17
WD_FORMAT_DOCX = 16
WD_ACTIVE_END_PAGE = 3      # wdActiveEndPageNumber
WD_GOTO_PAGE, WD_GOTO_ABSOLUTE = 1, 1


def _say(msg):
    """Console-safe print: the Windows console codepage cannot encode the
    nested-bullet glyphs, and a UnicodeEncodeError here would abort a report
    that is otherwise complete."""
    enc = sys.stdout.encoding or "utf-8"
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode(enc, "replace").decode(enc, "replace"))


def _word():
    try:
        import win32com.client as win32
    except ImportError:
        sys.exit("pywin32 not installed.  Run:  python -m pip install pywin32")
    try:
        app = win32.gencache.EnsureDispatch("Word.Application")
    except Exception as exc:                                   # noqa: BLE001
        sys.exit("Could not start Microsoft Word: %s\n"
                 "Fall back to build_resume.py's text-metric estimate and say "
                 "so explicitly." % exc)
    app.Visible = False
    app.DisplayAlerts = False
    return app


def inspect(path, pdf=None, png=None, docx=None):
    src = str(Path(path).resolve())
    app = _word()
    try:
        doc = app.Documents.Open(src, ReadOnly=False, AddToRecentFiles=False)
        try:
            pages = doc.ComputeStatistics(WD_STAT_PAGES)
            words = doc.ComputeStatistics(WD_STAT_WORDS)
            lines = doc.ComputeStatistics(WD_STAT_LINES)
            print("%s" % Path(src).name)
            print("  pages: %d   words: %d   lines: %d" % (pages, words, lines))

            # How full is the final page? Word gives us the last paragraph's
            # vertical position on its page, which is a real measurement.
            try:
                rng = doc.Content
                rng.Collapse(0)                                # wdCollapseEnd
                top = rng.Information(6)                       # wdVerticalPositionRelativeToPage
                usable = doc.PageSetup.PageHeight - doc.PageSetup.BottomMargin
                frac = max(0.0, min(1.0, float(top) / float(usable)))
                print("  last page is ~%.0f%% full" % (frac * 100))
                if pages > 1 and frac < 0.25:
                    print("  ! the final page is nearly empty - cut to %d pages "
                          "or add substance" % (pages - 1))
            except Exception:                                  # noqa: BLE001
                pass

            # Headings that landed at the very bottom of a page read as orphans
            # even with keep_with_next, so report where each page begins.
            starts = []
            for i in range(1, pages + 1):
                try:
                    r = doc.GoTo(WD_GOTO_PAGE, WD_GOTO_ABSOLUTE, i)
                    r.MoveEnd(1, 80)                           # wdCharacter
                    starts.append((i, r.Text.strip().replace("\r", " ")[:70]))
                except Exception:                              # noqa: BLE001
                    break
            if starts:
                print("  page breaks land here:")
                for i, txt in starts:
                    _say("    p%-2d starts: %s" % (i, txt))

            if docx:
                out = str(Path(docx).resolve())
                doc.SaveAs2(out, FileFormat=WD_FORMAT_DOCX)
                print("  converted -> %s" % out)
            if pdf:
                out = str(Path(pdf).resolve())
                Path(out).parent.mkdir(parents=True, exist_ok=True)
                doc.ExportAsFixedFormat(out, WD_FORMAT_PDF)
                print("  pdf -> %s" % out)
            if png:
                pdf_tmp = pdf or str(Path(png) / "_render.pdf")
                Path(png).mkdir(parents=True, exist_ok=True)
                if not pdf:
                    doc.ExportAsFixedFormat(str(Path(pdf_tmp).resolve()),
                                            WD_FORMAT_PDF)
                _render(pdf_tmp, png)
            return pages
        finally:
            doc.Close(False)
    finally:
        app.Quit()


def _render(pdf_path, outdir):
    """PDF -> one PNG per page, so the layout can actually be looked at."""
    try:
        import pypdfium2 as pdfium
    except ImportError:
        print("  (pypdfium2 not installed - skipping PNG render.  "
              "python -m pip install pypdfium2)")
        return
    doc = pdfium.PdfDocument(str(Path(pdf_path).resolve()))
    for i, page in enumerate(doc, 1):
        img = page.render(scale=110 / 72).to_pil()
        out = Path(outdir) / ("page-%02d.png" % i)
        img.save(out)
        print("  png -> %s" % out)


def main():
    ap = argparse.ArgumentParser(description="Real page counts and rendering "
                                             "for a resume, via Word.")
    ap.add_argument("input", help=".docx or legacy .doc")
    ap.add_argument("--pdf", help="export a PDF here")
    ap.add_argument("--png", help="render each page to PNG in this directory")
    ap.add_argument("--docx", help="save a .docx copy here (converts .doc)")
    a = ap.parse_args()
    inspect(a.input, pdf=a.pdf, png=a.png, docx=a.docx)


if __name__ == "__main__":
    main()
