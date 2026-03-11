# Daily Status Tracker Automation

This repository provides a simple Python automation to combine multiple team status files (Excel/CSV) into one master Excel with:

- `Completed` sheet (all completed tasks)
- `InProgress_or_Incomplete` sheet (all non-completed tasks)
- `Summary` sheet (counts by status and assignee)

## 1) Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Input format

Place all team files for the day/week in a folder (for example `input/`).

Supported formats:
- `.xlsx`
- `.xls`
- `.csv`

The script auto-maps common column variants to these canonical fields:
- `Assignee` (e.g., `name`, `owner`, `assigned to`)
- `Description` (e.g., `task`, `work item`, `summary`)
- `Status` (e.g., `state`)
- `Time` (e.g., `hours`, `effort`, `time spent`)

## 3) Run daily merge

```bash
python scripts/aggregate_status.py \
  --input-dir input \
  --output-file reports/daily_status_$(date +%F).xlsx \
  --mode daily
```

## 4) Run weekly merge

```bash
python scripts/aggregate_status.py \
  --input-dir weekly_input \
  --output-file reports/weekly_status_$(date +%F).xlsx \
  --mode weekly
```

Weekly mode creates the same sheets and includes week-level metrics in `Summary`.

## 5) Automation options

### Linux/macOS (cron)

Run every weekday at 6:30 PM:

```bash
crontab -e
```

Add:

```cron
30 18 * * 1-5 cd /workspace/DailyStatusTracker && /usr/bin/python3 scripts/aggregate_status.py --input-dir input --output-file reports/daily_status_$(date +\%F).xlsx --mode daily
```

### Windows (Task Scheduler)

Create a task that runs daily/weekly with:

- Program: `python`
- Arguments: `scripts/aggregate_status.py --input-dir input --output-file reports/daily_status_%DATE%.xlsx --mode daily`
- Start in: repository folder

## 6) Notes

- Completed status detection matches values like: `done`, `completed`, `closed`, `resolved`, `finished`.
- Non-completed statuses are grouped in `InProgress_or_Incomplete`.
- `Summary` includes:
  - total rows
  - completed rows
  - non-completed rows
  - unique assignees in completed/non-completed
  - count by status
  - count by assignee for non-completed tasks

## 7) Quick sample demo

If you want to quickly see what the output looks like, use the bundled sample:

```bash
python scripts/aggregate_status.py \
  --input-dir demo/input \
  --output-file demo/output_demo.xlsx \
  --mode daily
```

Then compare with:
- `demo/expected/Completed.csv`
- `demo/expected/InProgress_or_Incomplete.csv`
- `demo/README.md` (expected Summary values)
