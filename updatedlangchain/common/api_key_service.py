"""Shared API-key rotation service.

Discovers every `PREFIX` / `PREFIX_1` / `PREFIX_2` / ... variable in the
project `.env`, and retries a call with the next key when one fails.
Add `PREFIX_3=...` to `.env` and it is picked up automatically — no code change.

Usage from any notebook/script:

    from common.api_key_service import get_rapidapi_service, get_google_service

    rapidapi_service = get_rapidapi_service()
    data = rapidapi_service.call(lambda key: do_request(key))
"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv

# project root .env (this file lives at <root>/updatedlangchain/common/)
load_dotenv(Path(__file__).resolve().parents[2] / '.env')


class ApiKeyService:
    """Rotates over every `PREFIX` / `PREFIX_1` / `PREFIX_2` / ... env var.

    `call(fn)` runs `fn(key)` with the current key and falls over to the next
    one when `should_rotate(exc)` says the failure is key-related.
    """

    def __init__(self, prefix: str, should_rotate=None):
        self.prefix = prefix
        self.should_rotate = should_rotate or (lambda exc: True)
        pattern = re.compile(rf'^{re.escape(prefix)}(?:_(\d+))?$')
        found = sorted(
            (int(m.group(1) or 0), name, value)
            for name, value in os.environ.items()
            if (m := pattern.match(name)) and value
        )
        self.keys = [(name, value) for _, name, value in found]
        if not self.keys:
            raise RuntimeError(f'No env var matching {prefix} or {prefix}_N found')
        self._current = 0  # index of the last key that worked

    def call(self, fn):
        """fn(key) -> result. Starts at the last working key, rotates on failure."""
        last_exc = None
        for offset in range(len(self.keys)):
            i = (self._current + offset) % len(self.keys)
            name, key = self.keys[i]
            try:
                result = fn(key)
                self._current = i
                return result
            except Exception as exc:
                if not self.should_rotate(exc):
                    raise
                last_exc = exc
                print(f'  {name} failed ({exc}); rotating to next key')
        raise last_exc


def rotate_on_http_quota(exc) -> bool:
    """requests errors: 401/403 = bad/blocked key, 429 = quota or rate limit."""
    status = getattr(getattr(exc, 'response', None), 'status_code', None)
    return status in (401, 403, 429)


def rotate_on_gemini_quota(exc) -> bool:
    """Gemini/Google errors that another key can fix."""
    text = str(exc).lower()
    return any(s in text for s in ('429', 'quota', 'exhausted', 'rate limit', 'api key'))


_services: dict[str, ApiKeyService] = {}


def get_service(prefix: str, should_rotate=None) -> ApiKeyService:
    """Cached service per prefix, so all callers share rotation state."""
    if prefix not in _services:
        _services[prefix] = ApiKeyService(prefix, should_rotate)
    return _services[prefix]


def get_rapidapi_service() -> ApiKeyService:
    return get_service('RAPIDAPI_KEY', rotate_on_http_quota)


def get_google_service() -> ApiKeyService:
    return get_service('GOOGLE_API_KEY', rotate_on_gemini_quota)
