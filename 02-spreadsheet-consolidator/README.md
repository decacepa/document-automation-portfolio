# Spreadsheet consolidator

Merges a folder of individual monthly claim sheets into one master workbook — and flags every row
it cannot trust instead of quietly adding it to the total.

## The problem

Twelve people submit twelve spreadsheets. Someone opens each one, copies the rows into a master
file and sums it. The total has to reconcile exactly, so a single blank cell or a number typed as
text invalidates the whole submission — and neither is visible when you scroll past it.

The three defects that show up in real submissions, seeded here on purpose:

| Defect | What it does in a manual merge | What the script does |
|---|---|---|
| Blank value in a row | The row silently contributes zero | Flagged with file and row |
| Number stored as text | `SUM` ignores it; the total is short | Flagged with file and row |
| Duplicated entry | Paid twice | Flagged with file and row |

## Run it

```bash
pip install openpyxl
python generate_samples.py    # 12 fictional claim files, 3 with defects
python consolidate.py         # builds master_report.xlsx
```

Sample output:

```
consolidating 12 files
claim_9947290794.xlsx         14 valid rows
master written to master_report.xlsx
124 rows from 12 people · 3 issues flagged · 0.1s
issues need a human — see the Issues sheet
```

## What the master looks like

**Consolidated** — every valid row with its source file, so any number can be traced back to the
sheet it came from. Frozen header, live formulas.

**Issues** — one line per problem: which file, which row, what is wrong. This sheet is the point
of the tool. An empty Issues sheet is the only clean result.

## Design decisions

**Totals are formulas, not values.** The master uses `=F2*G2` and `=SUM(...)`, so it still
recalculates correctly after someone edits a cell. A workbook full of hardcoded numbers is a
snapshot, not a report.

**Bad rows are excluded, not corrected.** The script never guesses what a blank cell meant. It
leaves the row out of the total and names it on the Issues sheet, so the person who owns the
source file fixes it.

**Every row keeps its origin.** The source filename travels with the data into the master, which
is what makes an audit possible.

**Thresholds live in config.json** — first data row, cell references, maximum unit cost. Adapting
to a different form layout is a config change.

## A note on the data

All names, IDs and values are generated. No real submission appears in this repository.
