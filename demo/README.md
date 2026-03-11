# Sample demo

This folder contains a ready sample to understand what the aggregator generates.

## Input files
- `demo/input/alice_status.csv`
- `demo/input/bob_status.csv`

## Expected output sheets
- `demo/expected/Completed.csv`
- `demo/expected/InProgress_or_Incomplete.csv`

Expected `Summary` values for this sample:

| Metric | Value |
|---|---:|
| Mode | daily |
| Total tasks | 4 |
| Completed tasks | 2 |
| InProgress/Incomplete tasks | 2 |
| Unique people with completed tasks | 2 |
| Unique people with inprogress/incomplete tasks | 2 |

Status breakdown:
- Completed: 1
- Done: 1
- In Progress: 1
- Incomplete: 1

InProgress/Incomplete by assignee:
- Alice: 1
- Bob: 1

## Run with this sample

```bash
python scripts/aggregate_status.py \
  --input-dir demo/input \
  --output-file demo/output_demo.xlsx \
  --mode daily
```

After running, open `demo/output_demo.xlsx` and compare with the files in `demo/expected`.
