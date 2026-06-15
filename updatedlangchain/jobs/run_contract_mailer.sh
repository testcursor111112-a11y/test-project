#!/usr/bin/env bash
# Cron runner for the Zoho contract mailer.
# Executes the notebook in the uv project venv and appends all output to one log.
# COGS rows are appended by the notebook itself to <repo>/cogs/cogs_log.jsonl.
set -euo pipefail

REPO_ROOT="/Users/rasberry/Music/test/test-langchain"
JOBS_DIR="$REPO_ROOT/updatedlangchain/jobs"
LOG="$REPO_ROOT/cogs/cron_run.log"

mkdir -p "$(dirname "$LOG")"
cd "$JOBS_DIR"

echo "=== run $(date -u +%FT%TZ) ===" >> "$LOG"

# uv resolves the project venv (pyproject/uv.lock at REPO_ROOT).
# nbconvert must be installed there: `uv add nbconvert`
uv run --project "$REPO_ROOT" jupyter nbconvert \
  --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=1800 \
  --ExecutePreprocessor.kernel_name=python3 \
  company_contract_mailer_zoho.ipynb >> "$LOG" 2>&1

echo "=== done $(date -u +%FT%TZ) ===" >> "$LOG"
