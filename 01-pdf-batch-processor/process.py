"""
PDF batch processor.

Reads every PDF in the inbox, extracts the record ID from page 1, renames the
file to the required naming standard and compresses it below a hard size limit.
Anything it cannot handle is moved aside instead of being silently accepted.

All rules live in config.json, so the pipeline can be adapted to a new client
without touching this file.

Usage:
    python process.py
    python process.py --dry-run
"""

import argparse
import json
import logging
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from pypdf import PdfReader, PdfWriter

BASE = Path(__file__).parent


def load_config(path=BASE / "config.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def setup_logging(logfile):
    logfile = Path(logfile)
    logfile.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s %(message)s",
        handlers=[logging.FileHandler(logfile, encoding="utf-8"), logging.StreamHandler()],
    )


def extract_id(pdf_path, pattern, page_index=0):
    """Pull the record ID off the given page. Returns None if it is not there."""
    try:
        reader = PdfReader(str(pdf_path))
        text = reader.pages[page_index].extract_text() or ""
    except Exception as exc:  # unreadable or corrupt file
        logging.error("cannot read %s: %s", pdf_path.name, exc)
        return None

    match = re.search(pattern, text)
    return match.group(1) if match else None


def build_name(record_id, cfg):
    return cfg["naming"]["template"].format(
        id=record_id,
        year=cfg["naming"]["year"],
        term=cfg["naming"]["term"],
        code=cfg["naming"]["unit_code"],
    )


def compress(src, dst, max_bytes):
    """
    Shrink the file until it fits the limit.

    Step 1 recompresses the content streams with pypdf, which is lossless.
    Step 2 falls back to qpdf with object streams enabled.
    Returns the final size, or None if the file still does not fit.
    """
    writer = PdfWriter()
    writer.append(PdfReader(str(src)))
    for page in writer.pages:  # pages must belong to the writer before compressing
        page.compress_content_streams()
    writer.compress_identical_objects()
    with open(dst, "wb") as f:
        writer.write(f)

    if dst.stat().st_size <= max_bytes:
        return dst.stat().st_size

    tmp = dst.with_suffix(".tmp.pdf")
    try:
        subprocess.run(
            ["qpdf", "--object-streams=generate", "--recompress-flate",
             "--compression-level=9", str(dst), str(tmp)],
            check=True, capture_output=True,
        )
        tmp.replace(dst)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        logging.warning("qpdf pass skipped for %s (%s)", dst.name, exc)
        tmp.unlink(missing_ok=True)

    size = dst.stat().st_size
    return size if size <= max_bytes else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    args = parser.parse_args()

    cfg = load_config()
    setup_logging(BASE / cfg["paths"]["log_file"])

    inbox = BASE / cfg["paths"]["inbox"]
    outbox = BASE / cfg["paths"]["outbox"]
    quarantine = BASE / cfg["paths"]["quarantine"]
    max_bytes = cfg["limits"]["max_file_size_kb"] * 1024

    for folder in (outbox, quarantine):
        folder.mkdir(parents=True, exist_ok=True)

    files = sorted(inbox.glob("*.pdf"))
    if not files:
        logging.warning("no PDF files in %s — run generate_samples.py first", inbox)
        return

    started = datetime.now()
    logging.info("batch started — %d files, limit %d KB", len(files), cfg["limits"]["max_file_size_kb"])

    ok = failed = 0
    seen_ids = {}

    for src in files:
        record_id = extract_id(src, cfg["extraction"]["id_pattern"], cfg["extraction"]["page_index"])

        if not record_id:
            logging.error("%-30s no ID found on page 1 → quarantine", src.name)
            if not args.dry_run:
                shutil.copy2(src, quarantine / src.name)
            failed += 1
            continue

        if record_id in seen_ids:
            logging.error("%-30s duplicate ID %s (also in %s) → quarantine",
                          src.name, record_id, seen_ids[record_id])
            if not args.dry_run:
                shutil.copy2(src, quarantine / src.name)
            failed += 1
            continue

        seen_ids[record_id] = src.name
        new_name = build_name(record_id, cfg)

        if args.dry_run:
            logging.info("%-30s → %s  (dry run)", src.name, new_name)
            ok += 1
            continue

        dst = outbox / new_name
        size = compress(src, dst, max_bytes)

        if size is None:
            logging.error("%-30s → %s still above limit → quarantine", src.name, new_name)
            dst.unlink(missing_ok=True)
            shutil.copy2(src, quarantine / src.name)
            failed += 1
            continue

        logging.info("%-30s → %s  %.0f KB → %.0f KB",
                     src.name, new_name, src.stat().st_size / 1024, size / 1024)
        ok += 1

    elapsed = (datetime.now() - started).total_seconds()
    logging.info("batch finished — %d processed, %d quarantined, %.1fs", ok, failed, elapsed)


if __name__ == "__main__":
    main()
