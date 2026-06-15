"""COGS logger: append per-run LLM token usage + estimated cost to ONE JSONL file.

Cron-safe: opens the file in append mode and writes a single line per call, so
repeated runs (e.g. from cron) keep growing the same file instead of clobbering
it. The path is ABSOLUTE (`<repo-root>/cogs/cogs_log.jsonl`) so it stays the same
file regardless of the working directory cron uses. Override with `COGS_LOG_PATH`.

Usage from any notebook/script:

    from common.cogs_service import log_cogs
    log_cogs(model='gemini-3.1-flash-lite', input_tokens=1200,
             output_tokens=300, mails_sent=1)
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

# this file lives at <repo-root>/updatedlangchain/common/
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_LOG = _REPO_ROOT / 'cogs' / 'cogs_log.jsonl'

# USD per 1,000,000 tokens. EDIT to the model's real published rates.
PRICING = {
    'gemini-3.1-flash-lite': {'input': 0.10, 'output': 0.40},
}


def log_path() -> Path:
    """Resolve the append target, creating its parent dir on first use."""
    p = Path(os.getenv('COGS_LOG_PATH', _DEFAULT_LOG))
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """USD cost for a call; 0.0 for an unknown (unpriced) model."""
    rate = PRICING.get(model, {'input': 0.0, 'output': 0.0})
    return round(input_tokens / 1e6 * rate['input']
                 + output_tokens / 1e6 * rate['output'], 6)


def log_cogs(*, model: str, input_tokens: int, output_tokens: int,
             mails_sent: int, run: str = 'contract_mailer_zoho',
             extra: dict | None = None) -> dict:
    """Append one COGS record (timestamped JSON line) and return it."""
    input_tokens, output_tokens = int(input_tokens), int(output_tokens)
    record = {
        'ts': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'run': run,
        'model': model,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'total_tokens': input_tokens + output_tokens,
        'mails_sent': int(mails_sent),
        'est_cost_usd': estimate_cost(model, input_tokens, output_tokens),
    }
    if extra:
        record.update(extra)
    with open(log_path(), 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')
    return record
