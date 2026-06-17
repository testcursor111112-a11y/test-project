#!/usr/bin/env python
# coding: utf-8

# # Job Finder
# 
# Finds **remote** jobs posted in the **last 24 hours** for MERN / Full Stack / similar roles
# using the **JSearch API** (aggregates LinkedIn, Naukri, Indeed, remote boards via Google for Jobs)
# and appends new ones to a **Google Sheet**. A single Gemini call filters out
# irrelevant listings (internships, wrong stacks).
# 
# ## One-time setup
# 
# ### 1. RapidAPI key(s) (JSearch)
# 1. Sign up at https://rapidapi.com and subscribe to the **free** plan of
#    [JSearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch).
# 2. Free tier = 200 requests/month per key, so the notebook supports **multiple
#    numbered keys** and rotates to the next one automatically when one fails
#    (quota hit / blocked). Add to the project `.env`:
#    ```
#    RAPIDAPI_KEY_1=your_first_key
#    RAPIDAPI_KEY_2=your_second_key
#    # RAPIDAPI_KEY_3=... add more any time — picked up automatically, no code change
#    ```
#    The same pattern works for Gemini: `GOOGLE_API_KEY` (bare) and/or
#    `GOOGLE_API_KEY_1`, `GOOGLE_API_KEY_2`, ...
# 
# ### 2. Google Sheets service account
# 1. Go to https://console.cloud.google.com → create (or pick) a project.
# 2. **APIs & Services → Library** → enable **Google Sheets API** and **Google Drive API**.
# 3. **IAM & Admin → Service Accounts** → *Create service account* (any name) →
#    done. Open it → **Keys → Add key → JSON** → download.
# 4. Save the file as `service_account.json` in the **project root** (already gitignored),
#    and point `.env` at it:
#    ```
#    SERVICE_ACCOUNT_PATH=/absolute/path/to/repo/service_account.json
#    ```
# 5. Create a Google Sheet, copy its ID from the URL
#    (`https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit`), and **share the sheet
#    with the service account email** (`...@...iam.gserviceaccount.com`) as **Editor**.
# 6. Add to `.env`:
#    ```
#    SHEET_ID=your_sheet_id_here
#    ```

# In[34]:


import os
import sys
from pathlib import Path

# make ../ (updatedlangchain/) importable for the shared `common` package
try:
    script_dir = Path(__file__).resolve().parent
except NameError:
    script_dir = Path.cwd()
sys.path.append(str(script_dir.parent))

from common.api_key_service import get_rapidapi_service, get_google_service
from common.logging_service import get_logger

log = get_logger('job_finder')
rapidapi_service = get_rapidapi_service()
google_service = get_google_service()

SHEET_ID = os.getenv('SHEET_ID')

log.info('RapidAPI keys found: %s', [name for name, _ in rapidapi_service.keys])
log.info('Google keys found: %s', [name for name, _ in google_service.keys])
log.info('Sheet ID loaded: %s', SHEET_ID)


# ## Roles to search
# 
# Edit this list any time — one JSearch request per role per run.

# In[35]:


ROLES = [
    'MERN stack developer',
    'Full stack developer React Node.js',
    'Node.js backend developer',
    'React.js developer',
    'Full stack developer'
]

# Companies to skip on every run (spammy / repeated low-quality listings).
# Matched case-insensitively against employer_name (substring match).
BLOCKED_COMPANIES = {
    '2.halvolink',
    'careersprint',

}

# JSearch covers all publishers by default (LinkedIn, Naukri, Indeed, Glassdoor,
# remote boards, ...) — no platform filter needed.
# country param omitted -> JSearch default index; work_from_home=true keeps it remote-only.


# ## JSearch helper
# 
# `date_posted='today'` = posted within the last 24 hours.

# In[36]:


import time
import requests

JSEARCH_URL = 'https://jsearch.p.rapidapi.com/search'
JSEARCH_HOST = 'jsearch.p.rapidapi.com'


def search_jsearch(query: str) -> list[dict]:
    """Return remote jobs posted in the last 24h for one query."""
    params = {
        'query': query,
        'page': 1,
        'num_pages': 10,
        'date_posted': 'today',      # last 24 hours
        'work_from_home': 'true',    # remote only
    }

    def do_request(key: str) -> list[dict]:
        max_retries = 3
        backoff = 2
        for attempt in range(max_retries):
            try:
                resp = requests.get(
                    JSEARCH_URL,
                    headers={'X-RapidAPI-Key': key, 'X-RapidAPI-Host': JSEARCH_HOST},
                    params=params,
                    timeout=30,
                )
                resp.raise_for_status()
                return resp.json().get('data', [])
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if attempt == max_retries - 1:
                    raise
                log.warning("    Transient error: %s. Retrying in %ds...", e, backoff)
                time.sleep(backoff)
                backoff *= 2
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response is not None else None
                # Retry on rate limit (429) or server errors (5xx)
                if status_code in (429, 500, 502, 503, 504):
                    if attempt == max_retries - 1:
                        raise
                    log.warning("    HTTP %s error: %s. Retrying in %ds...", status_code, e, backoff)
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    raise

    return rapidapi_service.call(do_request)


# ## Google Sheets helper

# In[37]:


import os
import gspread

SHEET_HEADER = [
    'Date Added', 'Job Title', 'Company', 'Location', 'Remote',
    'Source', 'Posted At (UTC)', 'Employment Type', 'Apply Link',
    'Contact Email',
]

gc = gspread.service_account(filename=os.getenv('SERVICE_ACCOUNT_PATH', 'service_account.json'))
worksheet = gc.open_by_key(SHEET_ID).sheet1

# write/refresh header row
if worksheet.row_values(1) != SHEET_HEADER:
    worksheet.update(values=[SHEET_HEADER], range_name='A1')

log.info('Connected to sheet: %s', worksheet.spreadsheet.title)


# In[38]:


import os
print(os.getcwd())


# ## Pipeline
# 
# Plain functions, run in sequence:
# 
# ```
# fetch_all_jobs → dedupe → filter_relevant (Gemini) → add_to_sheet
# ```
# 
# - **fetch_all_jobs** — one JSearch call per role, remote-only, last 24h
# - **dedupe** — drops duplicates within the batch *and* anything already in the sheet
# - **filter_relevant** — one Gemini call keeps only jobs genuinely fitting a MERN / full-stack profile
# - **add_to_sheet** — appends the survivors to Google Sheets (with contact email when found)

# In[39]:


def fetch_all_jobs() -> list[dict]:
    """One JSearch call per role."""
    raw = []
    for role in ROLES:
        try:
            jobs = search_jsearch(role)
            log.info('  %r: %d jobs', role, len(jobs))
            raw.extend(jobs)
        except Exception as e:
            log.exception('  %r: request failed', role)
    return raw


# In[40]:


def is_blocked(job: dict) -> bool:
    """True if the job's company is in BLOCKED_COMPANIES (case-insensitive substring)."""
    name = (job.get('employer_name') or '').lower()
    return any(b in name for b in BLOCKED_COMPANIES)


def dedupe(raw_jobs: list[dict]) -> list[dict]:
    """Drop blocked companies, duplicates within the batch, and anything already in the sheet."""
    # links already in the sheet (column 9 = Apply Link)
    existing_links = set(worksheet.col_values(9)[1:])

    seen = set()
    new_jobs = []
    blocked = 0
    for job in raw_jobs:
        if is_blocked(job):
            blocked += 1
            continue
        key = job.get('job_apply_link') or (job.get('job_title'), job.get('employer_name'))
        if key in seen or job.get('job_apply_link') in existing_links:
            continue
        seen.add(key)
        new_jobs.append(job)

    log.info('  %d raw -> %d new (not in sheet, %d blocked)', len(raw_jobs), len(new_jobs), blocked)
    return new_jobs


# In[41]:


from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

GEMINI_MODEL = 'gemini-3.1-flash-lite'


class RelevantJobs(BaseModel):
    """Indices of jobs relevant to the candidate."""
    indices: list[int] = Field(description='0-based indices of the relevant jobs')


def gemini_filter(prompt: str) -> RelevantJobs:
    """Structured Gemini call through the rotating Google API keys."""
    def do_invoke(key: str) -> RelevantJobs:
        model = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=key)
        return model.with_structured_output(RelevantJobs).invoke(prompt)

    return google_service.call(do_invoke)


def filter_relevant(jobs: list[dict]) -> list[dict]:
    """One Gemini call: keep only jobs fitting a MERN / full-stack profile."""
    if not jobs:
        return []

    listing = '\n'.join(
        f'{i}. {j["job_title"]} at {j["employer_name"]} '
        f'({j.get("job_employment_type", "?")})'
        for i, j in enumerate(jobs)
    )
    prompt = (
        'The candidate is a MERN stack / full-stack JavaScript developer '
        '(MongoDB, Express, React, Node.js).\n'
        'From the numbered job list below, return the indices of jobs that are a '
        'genuine fit: developer roles centred on JavaScript/TypeScript, React, '
        'Node.js, MERN, or general full-stack web work.\n'
        'Exclude unrelated stacks (pure Java/.NET/PHP), non-developer roles, '
        'internships, and paid courses/certificates disguised as jobs.\n\n'
        f'{listing}'
    )
    result = gemini_filter(prompt)
    relevant = [jobs[i] for i in result.indices if 0 <= i < len(jobs)]
    log.info('  %d new -> %d relevant', len(jobs), len(relevant))
    return relevant


# In[42]:


import re
from datetime import datetime, timezone

EMAIL_RE = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
JUNK_EMAIL = ('noreply', 'no-reply', 'donotreply', 'example.com', 'sentry', 'support@')


def extract_contact_email(job: dict) -> str:
    """Pull recruiter/HR emails out of the job description, if any."""
    text = job.get('job_description', '') or ''
    emails = {
        e.lower() for e in EMAIL_RE.findall(text)
        if not any(j in e.lower() for j in JUNK_EMAIL)
    }
    return ', '.join(sorted(emails))


def add_to_sheet(jobs: list[dict]) -> int:
    """Append job rows to the Google Sheet."""
    rows = []
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
    for j in jobs:
        location = ', '.join(
            p for p in [j.get('job_city'), j.get('job_state'), j.get('job_country')] if p
        )
        rows.append([
            today,
            j.get('job_title', ''),
            j.get('employer_name', ''),
            location,
            'Yes' if j.get('job_is_remote') else 'No',
            j.get('job_publisher', ''),
            j.get('job_posted_at_datetime_utc', ''),
            j.get('job_employment_type', ''),
            j.get('job_apply_link', ''),
            extract_contact_email(j),
        ])

    if rows:
        worksheet.append_rows(rows, value_input_option='USER_ENTERED')
    log.info('  %d rows appended to sheet', len(rows))
    return len(rows)


# ## Email the BDE (Zoho)
# 
# After the run, email the BDE a summary + **today's openings as a CSV attachment**
# (no Drive link). Sent via Zoho SMTP, same pattern as the contract mailer.
# 
# Add to `.env`:
# ```
# ZOHO_SENDER_EMAIL=you@yourdomain.com
# ZOHO_APP_PASSWORD=your_zoho_app_password
# BDE_EMAIL=bde@yourdomain.com
# # optional overrides (defaults shown):
# # ZOHO_SMTP_SERVER=smtp.zoho.in
# # ZOHO_SMTP_PORT=587
# ```

# In[43]:


import io
import csv
import smtplib
from email.message import EmailMessage

ZOHO_SMTP_SERVER = os.getenv('ZOHO_SMTP_SERVER', 'smtp.zoho.in')
ZOHO_SMTP_PORT = int(os.getenv('ZOHO_SMTP_PORT', '587'))
ZOHO_SENDER_EMAIL = os.getenv('ZOHO_SENDER_EMAIL')
ZOHO_APP_PASSWORD = os.getenv('ZOHO_APP_PASSWORD')
BDE_EMAIL = os.getenv('BDE_EMAIL')

SHEET_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit'


def build_openings_csv(jobs: list[dict]) -> bytes:
    """Today's openings -> CSV bytes, same columns as the sheet."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(SHEET_HEADER)
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
    for j in jobs:
        location = ', '.join(
            p for p in [j.get('job_city'), j.get('job_state'), j.get('job_country')] if p
        )
        w.writerow([
            today,
            j.get('job_title', ''),
            j.get('employer_name', ''),
            location,
            'Yes' if j.get('job_is_remote') else 'No',
            j.get('job_publisher', ''),
            j.get('job_posted_at_datetime_utc', ''),
            j.get('job_employment_type', ''),
            j.get('job_apply_link', ''),
            extract_contact_email(j),
        ])
    return buf.getvalue().encode('utf-8')


def notify_bde(jobs: list[dict]) -> None:
    """Email the BDE a summary + today's openings as a CSV attachment."""
    if not jobs:
        log.info('  no new jobs -> skipping BDE email')
        return
    if not (ZOHO_SENDER_EMAIL and ZOHO_APP_PASSWORD and BDE_EMAIL):
        log.warning('  ZOHO_SENDER_EMAIL / ZOHO_APP_PASSWORD / BDE_EMAIL missing -> skipping email')
        return

    n = len(jobs)
    body = (
        'Hello,\n\n'
        'This is an automated update regarding new job postings.\n\n'
        f'We have found {n} new job(s).\n\n'
        f'You can review the latest All job listings here: {SHEET_URL}\n\n'
        "Today's openings are attached as a CSV.\n\n"
        'Please update the email list as needed, and the next job run will proceed shortly.\n\n'
        'Best regards,\n\n'
        'Your Automated Job Finder\n'
    )

    msg = EmailMessage()
    msg['From'] = ZOHO_SENDER_EMAIL
    msg['To'] = BDE_EMAIL
    msg['Subject'] = f'Found {n} job(s) from All'
    msg.set_content(body)

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    msg.add_attachment(
        build_openings_csv(jobs),
        maintype='text', subtype='csv',
        filename=f'job_openings_{today}.csv',
    )

    with smtplib.SMTP(ZOHO_SMTP_SERVER, ZOHO_SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(ZOHO_SENDER_EMAIL, ZOHO_APP_PASSWORD)
        smtp.send_message(msg)
    log.info('  emailed BDE (%s) — %d job(s), CSV attached', BDE_EMAIL, n)


# ## Run
# 
# Each run costs `len(ROLES)` JSearch requests (4 by default).
# Free tier = 200/month → ~50 runs, comfortably one per day.

# In[44]:


log.info('=== job_finder start ===')
log.info('Fetching...')
raw = fetch_all_jobs()

log.info('Deduping...')
new = dedupe(raw)

log.info('Filtering...')
relevant = filter_relevant(new)

log.info('Writing...')
added = add_to_sheet(relevant)

log.info('Emailing BDE...')
notify_bde(relevant)

log.info('Done. Jobs added to sheet: %d', added)
log.info('https://docs.google.com/spreadsheets/d/%s/edit', SHEET_ID)


# ## Daily automation (optional)
# 
# Export this notebook to a script and cron it:
# 
# ```bash
# jupyter nbconvert --to script job_finder_agent.ipynb
# # crontab -e  → run every day at 9am:
# # 0 9 * * * cd /Users/rasberry/Music/test/test-langchain/updatedlangchain/jobs && /Users/rasberry/Music/test/test-langchain/.venv/bin/python job_finder_agent.py
# ```
