# PDF batch processor

Takes a folder of inconsistently named scanned PDFs, reads the record ID off page 1 of each one,
renames every file to a strict standard and compresses it below a hard size limit.

Built for an archiving system that silently rejects anything above 400 KB or outside its naming
pattern — so a wrong filename is not a cosmetic problem, it is a lost document.

## The problem

| Before | After |
|---|---|
| `scan_0012.pdf` — 437 KB | `5942859575_2024_02_006502.pdf` — 252 KB |
| `IMG_20240115_0042.pdf` — 516 KB | `2382278555_2024_02_006502.pdf` — 298 KB |
| `Documento (3).pdf` — 398 KB | `4433344159_2024_02_006502.pdf` — 230 KB |
| `final ok v2 REVISED.pdf` — 320 KB | `1445763229_2024_02_006502.pdf` — 185 KB |

Doing this by hand: open each file, read the ID, retype it into a four-part filename, run it
through a compressor, check the size, repeat. A full working day for one batch.

With the script: **under a second per file, and no naming errors.**

## Run it

```bash
pip install pypdf reportlab
python generate_samples.py    # builds a messy inbox of fictional documents
python process.py             # processes the batch
python process.py --dry-run   # reports what it would do, writes nothing
```

Sample output:

```
batch started — 10 files, limit 400 KB
Documento (3).pdf              → 4433344159_2024_02_006502.pdf  398 KB → 230 KB
IMG_20240115_0042.pdf          → 2382278555_2024_02_006502.pdf  516 KB → 298 KB
form - signed.pdf              no ID found on page 1 → quarantine
batch finished — 9 processed, 1 quarantined, 0.3s
```

## Design decisions

**Nothing is guessed.** If the ID is not on page 1, the file goes to `quarantine/` and a human
looks at it. A pipeline that invents a filename is worse than one that stops.

**Duplicates are caught.** The same ID appearing twice in a batch usually means a file was
scanned twice — the second one is quarantined rather than overwriting the first.

**The rules are not in the code.** Naming template, ID pattern, size limit and folders all live
in `config.json`. A new client with a different standard needs a new config, not a new script.

**Compression is lossless.** Content streams are recompressed and objects deduplicated; the text
stays selectable and the pages stay readable. Files that still do not fit are quarantined instead
of being degraded.

**Everything is logged.** `logs/pipeline.log` records every file, its old and new size, and every
rejection — so the batch is auditable after the fact.

## Files

```
generate_samples.py   builds the fictional test inbox
process.py            the pipeline
config.json           all rules and paths
inbox/                input
outbox/               renamed and compressed output
quarantine/           files that need a human
logs/                 run log
```

## A note on the data

Every document, ID and name here is generated. No real file, person or organization appears in
this repository.
