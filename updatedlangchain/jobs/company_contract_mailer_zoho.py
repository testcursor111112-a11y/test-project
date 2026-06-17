#!/usr/bin/env python
# coding: utf-8

# # Lanatus Systems — Contract Opportunity Mailer (Zoho)
# 
# Sends outreach mails **on behalf of the company** offering contract development
# teams. For every job row that has a **Contact Email** but no **Contract Mail Sent At**:
# 
# 1. Researches the target company (DuckDuckGo)
# 2. Loads the **profile sheet** (`Name / Profile / Experience / URL / Available`) —
#    one person can have several profile variants with different experience; Gemini
#    picks the **single most suitable variant per person** for this job's role and
#    required experience
# 3. One Gemini call writes the personalized intro + picks the profiles; the rest of
#    the mail is a **fixed template** (same structure as our current outreach mail):
#    profile table with resume links, team achievements, call to action, signature
# 4. Sends via **Zoho SMTP** (STARTTLS, port 587; plain-text fallback + HTML), stamps the row
# 
# ## Setup
# 
# Reuses `.env` from the other notebooks (`SHEET_ID`, Gemini keys,
# `service_account.json`) plus the Zoho keys:
# ```
# ZOHO_SMTP_SERVER=smtp.zoho.in
# ZOHO_SMTP_PORT=587
# ZOHO_SENDER_EMAIL=connect@trylanatus.com
# ZOHO_APP_PASSWORD=your_zoho_app_password
# PROFILE_SHEET_ID=your_profile_sheet_id   # omit if profiles are a tab in the jobs spreadsheet
# ```
# Share the profile sheet with the service-account email too (Viewer is enough).

# In[1]:


import os
import sys
from pathlib import Path

# make ../ (updatedlangchain/) importable for the shared `common` package
try:
    script_dir = Path(__file__).resolve().parent
except NameError:
    script_dir = Path.cwd()
sys.path.append(str(script_dir.parent))

from common.api_key_service import get_google_service

google_service = get_google_service()

SHEET_ID = os.getenv('SHEET_ID')
PROFILE_SHEET_ID = os.getenv('PROFILE_SHEET_ID') or SHEET_ID
PROFILE_WORKSHEET = os.getenv('PROFILE_WORKSHEET')  # None -> first tab

# Zoho SMTP config (STARTTLS on 587)
ZOHO_SMTP_SERVER = os.getenv('ZOHO_SMTP_SERVER', 'smtp.zoho.in')
ZOHO_SMTP_PORT = int(os.getenv('ZOHO_SMTP_PORT', '587'))
ZOHO_SENDER_EMAIL = os.getenv('ZOHO_SENDER_EMAIL')
ZOHO_APP_PASSWORD = (os.getenv('ZOHO_APP_PASSWORD') or '').replace(' ', '')

print('Google keys found:', [name for name, _ in google_service.keys])
print('Jobs sheet loaded:', bool(SHEET_ID))
print('Profile sheet:', 'separate' if PROFILE_SHEET_ID != SHEET_ID else 'same spreadsheet')
print('Zoho configured:', bool(ZOHO_SENDER_EMAIL and ZOHO_APP_PASSWORD))


# ## Sender identity & team achievements
# 
# Edit here when the signature or the achievements list changes.

# In[2]:


SENDER = {
    'name': 'Maulik Shah',
    'role': 'Co-Founder',
    'company': 'Lanatus Systems',
    'phone': '+91 9316867779',
    'email': 'maulik@lanatussystems.com',
    'website': 'lanatussystems.com',
    'address': '1107, Shivalik Shilp 2, Opp. ITC Narmada Hotel, Vastrapur, Ahmedabad-380015, Gujarat (India)',
}

TEAM_PITCH = (
    'Our team excels in key tech stacks such as JavaScript (React/Node/Nest/Next), '
    'API Integration, and Cloud (AWS), alongside other robust technologies like '
    'PostgreSQL, MongoDB, and Angular. We are adept at building fast, scalable, '
    'and high-quality engineering solutions.'
)

ACHIEVEMENTS = [
    'Built 10+ web apps using React, Node.js, NestJS, and Next.js, significantly '
    'improving client workflow efficiency by 50%.',
    'Contributed to a SaaS platform supporting over 5,000 active users.',
    'Developed a robust solution for streaming 45+ cameras simultaneously using '
    'S3, EC2, and Node.js.',
    'Achieved a 66% reduction in server costs through database query optimization '
    'and migration to AWS.',
]

# Lanatus brand colors (site primary palette)
ACCENT = '#316bff'        # primary
ACCENT_DARK = '#134cdd'   # primary-400
TINT_1, TINT_2 = '#e9f3ff', '#fbfbfb'  # primary-100 -> near-white gradient

MAPS_URL = (
    'https://www.google.com/maps/place/Shivalik+Shilp+2/@23.0288856,72.5269333,17z/'
    'data=!3m1!4b1!4m6!3m5!1s0x395e84c8d4d4139d:0x177fd3db1f47ada6'
    '!8m2!3d23.0288856!4d72.5295082!16s%2Fg%2F11ckky9nzm?entry=ttu'
)

# real company signature (logo + socials), cleaned of Gmail proxy/markup junk
SIGNATURE_HTML = f"""<table cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-family:Arial,Helvetica,sans-serif;">
<tr>
  <td style="vertical-align:middle;padding:1px;width:73px;text-align:center;">
    <img src="https://d36urhup7zbd7q.cloudfront.net/a/cbcd949b-1754-4fdb-867b-eb870ab0051e.png"
         width="73" height="73" alt="Lanatus Systems"
         style="width:73px;height:73px;vertical-align:middle;border:none;">
  </td>
  <td style="padding:0 0 0 12px;vertical-align:top;">
    <table cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
      <tr><td style="line-height:1.08;padding:0 0 12px;border-bottom:1px solid #212121;">
        <span style="color:#45668e;font-weight:bold;font-size:14px;">{SENDER['name']}</span><br>
        <span style="font-weight:bold;color:#646464;line-height:1.2;font-size:13px;">{SENDER['role']} @ {SENDER['company']}</span>
      </td></tr>
      <tr><td style="padding-top:12px;font-size:11px;color:#212121;line-height:1.2;">
        <a href="tel:+919316867779" style="color:#212121;text-decoration:none;">{SENDER['phone']}</a>
        &nbsp;|&nbsp;
        <a href="https://{SENDER['website']}/" style="color:#212121;">{SENDER['website']}</a>
      </td></tr>
      <tr><td style="padding-top:5px;font-size:11px;line-height:1.2;">
        <a href="mailto:{SENDER['email']}" style="color:#212121;">{SENDER['email']}</a>
      </td></tr>
      <tr><td style="padding-top:5px;font-size:11px;line-height:1.2;">
        <a href="{MAPS_URL}" style="color:#212121;">{SENDER['address']}</a>
      </td></tr>
      <tr><td style="padding-top:12px;">
        <a href="https://m.facebook.com/profile.php?id=100083190858124" style="text-decoration:none;"><img
          src="https://cdn.gifo.wisestamp.com/s/fb/3b5998/48/circle/border.png"
          width="24" height="24" alt="Facebook" style="border:none;"></a>&nbsp;
        <a href="https://www.instagram.com/lanatussystems/" style="text-decoration:none;"><img
          src="https://cdn.gifo.wisestamp.com/s/inst/E4405F/48/circle/border.png"
          width="24" height="24" alt="Instagram" style="border:none;"></a>&nbsp;
        <a href="https://www.linkedin.com/company/lanatus/" style="text-decoration:none;"><img
          src="https://cdn.gifo.wisestamp.com/s/ld/0077b5/48/circle/border.png"
          width="24" height="24" alt="LinkedIn" style="border:none;"></a>
      </td></tr>
    </table>
  </td>
</tr>
</table>"""


# ## Jobs sheet: rows that still need a contract mail
# 
# Separate stamp column (**Contract Mail Sent At**, column L) so this campaign
# doesn't clash with the personal application mailer (column K).

# In[3]:


import os
import re
import gspread

COL_JOB_TITLE = 2        # B
COL_COMPANY = 3          # C
COL_LOCATION = 4         # D
COL_APPLY_LINK = 9       # I
COL_CONTACT_EMAIL = 10   # J
COL_CONTRACT_SENT = 12   # L

EMAIL_RE = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')

gc = gspread.service_account(filename=os.getenv('SERVICE_ACCOUNT_PATH', 'service_account.json'))
jobs_ws = gc.open_by_key(SHEET_ID).sheet1

if jobs_ws.cell(1, COL_CONTRACT_SENT).value != 'Contract Mail Sent At':
    jobs_ws.update_cell(1, COL_CONTRACT_SENT, 'Contract Mail Sent At')


def get_pending_jobs() -> list[dict]:
    """Rows with a contact email and no Contract Mail Sent At stamp."""
    pending = []
    for row_idx, row in enumerate(jobs_ws.get_all_values()[1:], start=2):
        row += [''] * (COL_CONTRACT_SENT - len(row))
        emails = EMAIL_RE.findall(row[COL_CONTACT_EMAIL - 1])
        if not emails or row[COL_CONTRACT_SENT - 1].strip():
            continue
        pending.append({
            'row': row_idx,
            'title': row[COL_JOB_TITLE - 1],
            'company': row[COL_COMPANY - 1],
            'location': row[COL_LOCATION - 1],
            'emails': emails,
        })
    return pending


pending = get_pending_jobs()
print(f'{len(pending)} jobs pending contract mail')
for job in pending:
    print(f"  row {job['row']}: {job['title']} @ {job['company']} -> {job['emails']}")


# ## Profile sheet: available developer profiles
# 
# Columns: `Name | Profile | Experience | URL | Available`. One person can appear
# several times with different profile variants — selection happens later, per job.

# In[4]:


TRUTHY = {'yes', 'y', 'true', '1', 'available'}


def load_profiles() -> list[dict]:
    """Available profile rows, normalized."""
    book = gc.open_by_key(PROFILE_SHEET_ID)
    ws = book.worksheet(PROFILE_WORKSHEET) if PROFILE_WORKSHEET else book.sheet1
    profiles = []
    for rec in ws.get_all_records():
        rec = {str(k).strip().lower(): v for k, v in rec.items()}
        if str(rec.get('available', '')).strip().lower() not in TRUTHY:
            continue
        exp_match = re.search(r'\d+(?:\.\d+)?', str(rec.get('experience', '')))
        profiles.append({
            'name': str(rec.get('name', '')).strip(),
            'profile': str(rec.get('profile', '')).strip(),
            'experience': float(exp_match.group()) if exp_match else 0,
            'url': str(rec.get('url', '')).strip(),
        })
    return [p for p in profiles if p['name'] and p['url']]


profiles = load_profiles()
print(f'{len(profiles)} available profiles')
for p in profiles:
    print(f"  {p['name']} — {p['profile']} — {p['experience']:g} yrs")


# ## Research the target company

# In[5]:


from ddgs import DDGS
from common.logging_service import get_logger

log = get_logger()


def research_company(company: str) -> str:
    """Collect search snippets about the company: what it does, stack, news."""
    queries = [
        f'"{company}" company about',
        f'"{company}" products services technology stack',
    ]
    snippets = []
    with DDGS() as ddgs:
        for query in queries:
            try:
                for hit in ddgs.text(query, max_results=4):
                    snippets.append(f"- {hit['title']}: {hit['body']}")
            except Exception:
                log.exception('  company search failed for %r', query)
    seen = set()
    unique = [s for s in snippets if not (s in seen or seen.add(s))]
    return '\n'.join(unique[:10]) or '(no search results found)'


# ## One Gemini call per job: personalize intro + pick profiles
# 
# Returns the two company-specific paragraphs and the indices of the most suitable
# profile variants — **at most one variant per person**, matched to the job's role
# and seniority. The rest of the mail is template, built in code.

# In[6]:


from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from common.logging_service import get_logger

log = get_logger()
GEMINI_MODEL = 'gemini-3.1-flash-lite'


class ContractMail(BaseModel):
    """Personalized parts of the contract outreach mail."""
    subject: str = Field(description='Email subject line')
    intro_paragraph: str = Field(description=(
        'First paragraph: who we are + something specific and positive about the '
        'target company from the research'))
    alignment_paragraph: str = Field(description=(
        'Short second paragraph: why our team fits their mission/role'))
    closing_paragraph: str = Field(description=(
        'Paragraph before the call-to-action: how we can support their projects, '
        'referencing the role/company specifics'))
    profile_indices: list[int] = Field(description=(
        '0-based indices of the chosen profile variants, at most one per person'))


def toon_profiles(profiles: list[dict]) -> str:
    """Compact TOON-style tabular block: declare fields once, one CSV row per variant.
    `i` is the 0-based index referenced by profile_indices. Cheaper than repeating
    field labels/separators on every row."""
    lines = [f"profiles[{len(profiles)}]{{i,name,profile,exp_years}}:"]
    for i, p in enumerate(profiles):
        prof = p['profile'].replace('"', "'")  # avoid breaking the quoted field
        lines.append(f'{i},{p["name"]},"{prof}",{p["experience"]:g}')
    return '\n'.join(lines)


def personalize(job: dict, research: str, profiles: list[dict]) -> tuple[ContractMail, dict]:
    listing = toon_profiles(profiles)
    prompt = f"""We are {SENDER['company']}, an agency providing skilled development teams for
contract-based collaborations. {SENDER['name']} ({SENDER['role']}) is writing an
outreach mail to the company below, which posted a job — we offer our contract
team instead of a single hire.

TARGET JOB:
- Title: {job['title']}
- Company: {job['company']}
- Location: {job['location'] or 'Remote'}

COMPANY RESEARCH (web snippets — use only facts clearly about this company;
ignore anything that looks like a different company with a similar name):
{research}

OUR TEAM PITCH (context): {TEAM_PITCH}

AVAILABLE PROFILE VARIANTS — TOON tabular. First line declares the row count and
fields `profiles[N]{{i,name,profile,exp_years}}:`; each following line is one
variant as CSV (`profile` is quoted). `i` is the 0-based index to return in
profile_indices. One person may appear in multiple rows with different
experience/role variants:
{listing}

TASKS:
1. subject — professional outreach subject, mentions {SENDER['company']} and the
   kind of team we offer for their role. No clickbait.
2. intro_paragraph — like: 'My name is {SENDER['name']}, and I'm reaching out as
   {SENDER['role']} of {SENDER['company']}. We specialize in providing highly
   skilled development teams for contract-based collaborations, and we've been
   impressed by <specific, REAL facts about the company from the research —
   their products, platform, approach>.' If research is empty/off-topic, praise
   the role's ambitions instead — do NOT invent facts.
3. alignment_paragraph — 1-2 sentences: our capabilities align with their
   mission (reference research if possible).
4. closing_paragraph — 2-3 sentences: how our collective experience can support
   their projects, referencing the role.
5. profile_indices — pick the profiles that best fit this job's tech stack and
   seniority. RULES: at most ONE variant per person (pick the variant whose role
   and experience best match the job); only relevant roles; if the job title
   implies seniority (senior/lead) prefer higher experience variants; 3 to 7
   profiles total.

Tone: professional, confident, concrete. No placeholders, no invented facts."""

    def do_invoke(key: str):
        model = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=key)
        # include_raw=True -> dict with 'parsed' (pydantic) and 'raw' (AIMessage w/ usage)
        return model.with_structured_output(ContractMail, include_raw=True).invoke(prompt)

    out = google_service.call(do_invoke)
    result: ContractMail = out['parsed']

    # pull token usage off the raw AIMessage
    raw = out.get('raw')
    usage = dict(getattr(raw, 'usage_metadata', None) or {})
    usage = {
        'input_tokens': usage.get('input_tokens', 0),
        'output_tokens': usage.get('output_tokens', 0),
        'total_tokens': usage.get('total_tokens',
                                  usage.get('input_tokens', 0) + usage.get('output_tokens', 0)),
        'model': GEMINI_MODEL,
    }
    log.info('  LLM tokens [%s]: in=%d out=%d total=%d', GEMINI_MODEL,
             usage['input_tokens'], usage['output_tokens'], usage['total_tokens'])

    # enforce the one-variant-per-person rule even if the model slips
    chosen, seen_names = [], set()
    for i in result.profile_indices:
        if 0 <= i < len(profiles) and profiles[i]['name'] not in seen_names:
            seen_names.add(profiles[i]['name'])
            chosen.append(i)
    result.profile_indices = chosen
    return result, usage


# ## Build the mail from the template
# 
# Fixed structure in code — only the intro/alignment/closing paragraphs and the
# profile table rows change per company. Resume URLs become links in the table.

# In[7]:


from html import escape


def build_html(job: dict, mail: ContractMail, chosen: list[dict]) -> str:
    rows = ''.join(
        f'<tr>'
        f'<td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;">{escape(p["name"])}</td>'
        f'<td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;">{escape(p["profile"])}</td>'
        f'<td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:center;">{p["experience"]:g} yrs</td>'
        f'<td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;">'
        f'<a href="{escape(p["url"])}" style="color:{ACCENT};">View resume</a></td>'
        f'</tr>'
        for p in chosen
    )
    achievements = ''.join(
        f'<li style="margin-bottom:6px;">{escape(a)}</li>' for a in ACHIEVEMENTS
    )
    return f"""<!DOCTYPE html>
<html><body style="margin:0;padding:24px 0;background-color:{TINT_1};background:linear-gradient(135deg,{TINT_1},{TINT_2});font-family:Arial,Helvetica,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center">
<table role="presentation" width="720" cellpadding="0" cellspacing="0" style="max-width:720px;background:#ffffff;border-radius:8px;overflow:hidden;">
<tr><td style="background:{ACCENT};padding:18px 28px;">
  <div style="color:#ffffff;font-size:18px;font-weight:bold;">{escape(SENDER['company'])}</div>
  <div style="color:#e9f3ff;font-size:13px;">Contract development teams · {escape(job['title'])}</div>
</td></tr>
<tr><td style="padding:28px;color:#333;font-size:14px;line-height:1.6;">
  <p style="margin-top:0;">Hi {escape(job['company'])} Team,</p>
  <p>{escape(mail.intro_paragraph)}</p>
  <p>{escape(mail.alignment_paragraph)}</p>
  <p style="margin-bottom:6px;"><strong>Developers available for immediate engagement:</strong></p>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-size:13px;border:1px solid #e5e7eb;border-radius:6px;">
    <tr style="background:{TINT_1};">
      <th align="left" style="padding:8px 12px;">Name</th>
      <th align="left" style="padding:8px 12px;">Profile</th>
      <th style="padding:8px 12px;">Experience</th>
      <th align="left" style="padding:8px 12px;">Resume</th>
    </tr>
    {rows}
  </table>
  <p>{escape(TEAM_PITCH)}</p>
  <p style="margin-bottom:6px;"><strong>Notable projects &amp; achievements by our team:</strong></p>
  <ul style="margin-top:0;padding-left:20px;">{achievements}</ul>
  <p>{escape(mail.closing_paragraph)}</p>
  <p>Would you be open to a brief call to discuss how our team can support your
  current and upcoming projects?</p>
  <p style="margin-bottom:16px;">Best regards,</p>
  {SIGNATURE_HTML}
</td></tr>
</table>
</td></tr></table>
</body></html>"""


def build_plain(job: dict, mail: ContractMail, chosen: list[dict]) -> str:
    table = '\n'.join(
        f"- {p['name']} | {p['profile']} | {p['experience']:g} yrs | {p['url']}"
        for p in chosen
    )
    achievements = '\n'.join(f'- {a}' for a in ACHIEVEMENTS)
    return f"""Hi {job['company']} Team,

{mail.intro_paragraph}

{mail.alignment_paragraph}

Developers available for immediate engagement:
{table}

{TEAM_PITCH}

Notable projects & achievements by our team:
{achievements}

{mail.closing_paragraph}

Would you be open to a brief call to discuss how our team can support your
current and upcoming projects?

Best regards,
{SENDER['name']}
{SENDER['role']} @ {SENDER['company']}
{SENDER['phone']} |  {SENDER['website']}

{SENDER['email']}

{SENDER['address']}"""


# ## Send via Zoho SMTP (STARTTLS, port 587)

# In[ ]:


import smtplib
import mimetypes
import requests
from email.message import EmailMessage
from common.logging_service import get_logger

log = get_logger()


def _resume_download_url(url: str) -> str:
    """Turn a Google Drive 'view' link into a direct-download URL; pass others through."""
    if 'drive.google.com' in url:
        m = re.search(r'/file/d/([\w-]+)', url) or re.search(r'[?&]id=([\w-]+)', url)
        if m:
            return f'https://drive.google.com/uc?export=download&id={m.group(1)}'
    return url


def fetch_resume(name: str, url: str) -> tuple[bytes, str, str] | None:
    """Download a resume -> (data, filename, mimetype). None on failure."""
    try:
        r = requests.get(_resume_download_url(url), timeout=30, allow_redirects=True)
        r.raise_for_status()
        data = r.content
        if not data:
            log.warning('    empty resume body for %s (%s)', name, url)
            return None
        ctype = (r.headers.get('Content-Type') or '').split(';')[0].strip() \
            or 'application/octet-stream'
        # filename: Content-Disposition -> else derive from name + type
        disp = r.headers.get('Content-Disposition', '')
        m = re.search(r'filename\*?=(?:UTF-8\'\')?\"?([^\";]+)', disp)
        if m:
            filename = m.group(1)
        else:
            ext = mimetypes.guess_extension(ctype) or '.pdf'
            safe = re.sub(r'[^A-Za-z0-9_-]+', '_', name).strip('_') or 'resume'
            filename = f'{safe}_resume{ext}'
        return data, filename, ctype
    except Exception:
        log.exception('    resume fetch failed for %s (%s)', name, url)
        return None


def build_message(to_addrs: list[str], subject: str, plain: str, html: str,
                  chosen: list[dict] | None = None) -> EmailMessage:
    msg = EmailMessage()
    msg['From'] = f"{SENDER['name']} <{ZOHO_SENDER_EMAIL}>"
    msg['To'] = ', '.join(to_addrs)
    msg['BCC'] = ', '.join(["bde@lanatussystems.com"])
    msg['Subject'] = subject
    msg.set_content(plain)
    msg.add_alternative(html, subtype='html')

    # attach each chosen profile's resume (links stay in the body too)
    for p in (chosen or []):
        att = fetch_resume(p['name'], p['url'])
        if not att:
            continue
        data, filename, ctype = att
        maintype, _, subtype = ctype.partition('/')
        msg.add_attachment(data, maintype=maintype or 'application',
                           subtype=subtype or 'octet-stream', filename=filename)
        log.info('    attached: %s (%d bytes)', filename, len(data))
    return msg


def send_mail(msg: EmailMessage) -> None:
    with smtplib.SMTP(ZOHO_SMTP_SERVER, ZOHO_SMTP_PORT) as smtp:
        smtp.starttls()  # upgrade to secure TLS
        smtp.login(ZOHO_SENDER_EMAIL, ZOHO_APP_PASSWORD)
        smtp.send_message(msg)


# ## Run
# 
# **`DRY_RUN = True`** (default) — writes every mail and saves it to
# `previews/contract_<company>.html`, sends nothing, stamps nothing. Check the
# previews (chosen profiles printed per job), then flip to `False` and re-run.

# In[10]:


from datetime import datetime, timezone
from common.cogs_service import log_cogs
from common.logging_service import get_logger

log = get_logger()

DRY_RUN = False
MAX_MAILS_PER_RUN = 10  # safety cap

PREVIEW_DIR = script_dir / 'previews'
PREVIEW_DIR.mkdir(exist_ok=True)

log.info('=== contract_mailer_zoho start (dry_run=%s) ===', DRY_RUN)
try:
    pending = get_pending_jobs()
    profiles = load_profiles()
except Exception:
    log.exception('startup failed loading jobs/profiles sheet')
    raise

log.info('%d pending, %d available profiles, sending up to %d',
         len(pending), len(profiles), MAX_MAILS_PER_RUN)

sent = 0
tok_in = tok_out = tok_total = 0  # cumulative LLM token usage
for job in pending[:MAX_MAILS_PER_RUN]:
    log.info('job row %s: %s @ %s -> %s',
             job['row'], job['title'], job['company'], job['emails'])

    try:
        research = research_company(job['company'])
        mail, usage = personalize(job, research, profiles)
    except Exception:
        log.exception('  personalize failed for row %s (%s) -> skipped',
                      job['row'], job['company'])
        continue

    tok_in += usage['input_tokens']
    tok_out += usage['output_tokens']
    tok_total += usage['total_tokens']
    chosen = [profiles[i] for i in mail.profile_indices]

    if not chosen:
        log.warning('  no suitable profiles for row %s -> skipped', job['row'])
        continue

    log.info('  subject: %s', mail.subject)
    log.info('  profiles: %s', ', '.join(
        f"{p['name']} ({p['profile']}, {p['experience']:g}y)" for p in chosen))

    html = build_html(job, mail, chosen)
    plain = build_plain(job, mail, chosen)

    safe_name = re.sub(r'[^A-Za-z0-9_-]+', '_', job['company']).strip('_') or f"row{job['row']}"
    preview = PREVIEW_DIR / f'contract_{safe_name}.html'
    preview.write_text(html, encoding='utf-8')
    log.info('  preview written: %s', preview)

    if DRY_RUN:
        continue

    try:
        send_mail(build_message(job['emails'], mail.subject, plain, html, chosen))
    except Exception:
        log.exception('  SEND FAILED for row %s (%s)', job['row'], job['company'])
        continue

    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
    try:
        jobs_ws.update_cell(job['row'], COL_CONTRACT_SENT, stamp)
    except Exception:
        log.exception('  stamp FAILED for row %s (mail WAS already sent!)', job['row'])
    sent += 1
    log.info('  sent + row %s stamped', job['row'])

log.info('Done. Mails sent: %d', sent)
log.info('LLM token usage [%s] total: in=%d out=%d total=%d',
         GEMINI_MODEL, tok_in, tok_out, tok_total)
if sent:
    log.info('  avg per mail: in=%d out=%d total=%d',
             tok_in // sent, tok_out // sent, tok_total // sent)

# append this run's COGS (token load + cost) to the single shared log file
try:
    cogs = log_cogs(model=GEMINI_MODEL, input_tokens=tok_in, output_tokens=tok_out,
                    mails_sent=sent, extra={'dry_run': DRY_RUN,
                                            'jobs_seen': len(pending[:MAX_MAILS_PER_RUN])})
    log.info('COGS appended: $%s (%d tok)', cogs['est_cost_usd'], cogs['total_tokens'])
except Exception:
    log.exception('COGS append failed')

