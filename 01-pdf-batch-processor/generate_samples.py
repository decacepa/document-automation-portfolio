"""
Generate the messy sample inbox used to demonstrate the pipeline.

Everything here is fictional: random IDs, random names, random values.
No real document, person or organization is involved.

Usage:
    python generate_samples.py
"""

import random
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

INBOX = Path(__file__).parent / "inbox"

# Deliberately inconsistent filenames, the way a scanner and five different
# people actually leave them.
MESSY_NAMES = [
    "scan_0012.pdf",
    "IMG_20240115_0042.pdf",
    "Documento (3).pdf",
    "final ok v2 REVISED.pdf",
    "new scan (copy).pdf",
    "digitalizacao 15-01.pdf",
    "doc1.pdf",
    "SCAN_2024_january_last.pdf",
    "untitled folder 4.pdf",
    "form - signed.pdf",
]

FIRST = ["Alex", "Jordan", "Morgan", "Casey", "Riley", "Taylor", "Jamie", "Avery", "Quinn", "Reese"]
LAST = ["Silva", "Nguyen", "Okafor", "Mendes", "Kowalski", "Ferreira", "Haddad", "Lima", "Osei", "Barros"]


def draw_page_one(c, record_id, name, year, term):
    """A page that looks like a scanned administrative form."""
    w, h = A4
    c.setFont("Helvetica-Bold", 13)
    c.drawString(25 * mm, h - 30 * mm, "PERSONNEL RECORD SHEET")
    c.setFont("Helvetica", 9)
    c.drawString(25 * mm, h - 36 * mm, f"Reporting period: {term}/{year}")
    c.line(25 * mm, h - 39 * mm, w - 25 * mm, h - 39 * mm)

    c.setFont("Helvetica", 11)
    # The ID is the only thing the pipeline needs, and it is always on page 1.
    c.drawString(25 * mm, h - 52 * mm, f"ID NUMBER: {record_id}")
    c.drawString(25 * mm, h - 60 * mm, f"NAME: {name}")
    c.drawString(25 * mm, h - 68 * mm, f"UNIT CODE: 006502")

    c.setFont("Helvetica", 9)
    y = h - 85 * mm
    for label in ("Position", "Start date", "Status", "Supervisor", "Remarks"):
        c.drawString(25 * mm, y, f"{label}: " + "".join(random.choice("ABCDEFGH") for _ in range(12)))
        y -= 7 * mm

    # Filler blocks so the file has realistic weight.
    c.setFont("Helvetica", 7)
    for i in range(28):
        c.drawString(25 * mm, y - i * 4 * mm, " ".join(
            "".join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(random.randint(3, 9)))
            for _ in range(16)
        ))


def draw_filler_page(c):
    """A dense page of text, the way a scanned dossier page looks to a parser."""
    w, h = A4
    c.setFont("Helvetica", 5)
    for i in range(150):
        c.drawString(35, h - 40 - i * 5.2, " ".join(
            "".join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(5))
            for _ in range(38)
        ))


def main(count=10, seed=7):
    random.seed(seed)
    INBOX.mkdir(exist_ok=True)
    for old in INBOX.glob("*.pdf"):
        old.unlink()

    used_ids = set()
    for i in range(count):
        while True:
            record_id = str(random.randint(1000000000, 9999999999))
            if record_id not in used_ids:
                used_ids.add(record_id)
                break

        name = f"{random.choice(FIRST)} {random.choice(LAST)}"
        path = INBOX / MESSY_NAMES[i % len(MESSY_NAMES)]

        # pageCompression=0 reproduces the bloated output most scanners produce:
        # correct content, no stream compression, files far above the size limit.
        c = canvas.Canvas(str(path), pagesize=A4, pageCompression=0)

        # One file in every batch is the wrong document: no ID on page 1.
        # The pipeline must catch it instead of guessing a filename.
        if i == count - 1:
            c.setFont("Helvetica-Bold", 13)
            c.drawString(25 * mm, A4[1] - 30 * mm, "BLANK COVER SHEET")
            record_id = "(none)"
        else:
            draw_page_one(c, record_id, name, 2024, "02")
        c.showPage()
        for _ in range(random.randint(8, 14)):
            draw_filler_page(c)
            c.showPage()
        c.save()

        print(f"created {path.name:32} id={record_id}  {path.stat().st_size / 1024:.0f} KB")

    print(f"\n{count} sample files in {INBOX}/")


if __name__ == "__main__":
    main()
