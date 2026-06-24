#!/usr/bin/env python
# coding: utf-8
"""LinkedIn job scraper (library).

Python port of the Node.js `linkedin-jobs-api`. Scrapes the LinkedIn guest
job-search endpoint and parses results with BeautifulSoup.

Features:
- In-memory TTL cache (1h)
- Batched pagination (25/page)
- Retry with exponential backoff
- Random User-Agent rotation

Usage:
    from linkedin_scrapper import query
    jobs = query({
        "keyword": "full stack developer",
        "location": "India",
        "dateSincePosted": "24hr",
        "remoteFilter": "remote",
        "limit": 25,
    })

Each job is a dict: position, company, location, date, salary, jobUrl,
companyLogo, agoTime.

Deps: requests, beautifulsoup4
"""

import time
import random
import logging
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# --- Random User-Agent ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
]


def get_random_user_agent():
    return random.choice(USER_AGENTS)


# --- Cache (TTL) ---
class JobCache:
    def __init__(self, ttl_seconds=60 * 60):
        self.cache = {}
        self.ttl = ttl_seconds

    def set(self, key, value):
        self.cache[key] = {"data": value, "timestamp": time.time()}

    def get(self, key):
        item = self.cache.get(key)
        if not item:
            return None
        if time.time() - item["timestamp"] > self.ttl:
            del self.cache[key]
            return None
        return item["data"]

    def clear(self):
        """Drop only expired entries (matches JS clear())."""
        now = time.time()
        expired = [k for k, v in self.cache.items() if now - v["timestamp"] > self.ttl]
        for k in expired:
            del self.cache[k]

    def size(self):
        return len(self.cache)


cache = JobCache()


# --- Filter mappings ---
DATE_RANGE = {
    "past month": "r2592000",
    "past week": "r604800",
    "24hr": "r86400",
}

EXPERIENCE_RANGE = {
    "internship": "1",
    "entry level": "2",
    "associate": "3",
    "senior": "4",
    "director": "5",
    "executive": "6",
}

JOB_TYPE_RANGE = {
    "full time": "F",
    "full-time": "F",
    "part time": "P",
    "part-time": "P",
    "contract": "C",
    "temporary": "T",
    "volunteer": "V",
    "internship": "I",
}

REMOTE_FILTER_RANGE = {
    "on-site": "1",
    "on site": "1",
    "remote": "2",
    "hybrid": "3",
}

SALARY_RANGE = {
    "40000": "1",
    "60000": "2",
    "80000": "3",
    "100000": "4",
    "120000": "5",
}


class Query:
    def __init__(self, query_obj):
        self.host = query_obj.get("host", "www.linkedin.com")
        self.keyword = (query_obj.get("keyword") or "").strip().replace(" ", "+")
        self.location = (query_obj.get("location") or "").strip().replace(" ", "+")
        self.date_since_posted = query_obj.get("dateSincePosted", "")
        self.job_type = query_obj.get("jobType", "")
        self.remote_filter = query_obj.get("remoteFilter", "")
        self.salary = query_obj.get("salary", "")
        self.experience_level = query_obj.get("experienceLevel", "")
        self.sort_by = query_obj.get("sortBy", "")
        self.limit = int(query_obj.get("limit") or 0)
        self.page = int(query_obj.get("page") or 0)
        self.has_verification = query_obj.get("has_verification", False)
        self.under_10_applicants = query_obj.get("under_10_applicants", False)

    # --- filter mappers ---
    def get_date_since_posted(self):
        return DATE_RANGE.get(self.date_since_posted.lower(), "")

    def get_experience_level(self):
        return EXPERIENCE_RANGE.get(self.experience_level.lower(), "")

    def get_job_type(self):
        return JOB_TYPE_RANGE.get(self.job_type.lower(), "")

    def get_remote_filter(self):
        return REMOTE_FILTER_RANGE.get(self.remote_filter.lower(), "")

    def get_salary(self):
        return SALARY_RANGE.get(str(self.salary), "")

    def get_page(self):
        return self.page * 25

    def get_cache_key(self):
        return f"{self.url(0)}_limit:{self.limit}"

    # --- URL builder ---
    def url(self, start=0):
        base = f"https://{self.host}/jobs-guest/jobs/api/seeMoreJobPostings/search?"
        params = []  # list of tuples to preserve order, like URLSearchParams

        if self.keyword:
            params.append(("keywords", self.keyword))
        if self.location:
            params.append(("location", self.location))
        if self.get_date_since_posted():
            params.append(("f_TPR", self.get_date_since_posted()))
        if self.get_salary():
            params.append(("f_SB2", self.get_salary()))
        if self.get_experience_level():
            params.append(("f_E", self.get_experience_level()))
        if self.get_remote_filter():
            params.append(("f_WT", self.get_remote_filter()))
        if self.get_job_type():
            params.append(("f_JT", self.get_job_type()))
        # NOTE: JS appended these unconditionally because non-empty strings
        # ("true"/"false") are truthy. Only send when the flag is actually set.
        if self.has_verification:
            params.append(("f_VJ", "true"))
        if self.under_10_applicants:
            params.append(("f_EA", "true"))

        params.append(("start", start + self.get_page()))

        if self.sort_by == "recent":
            params.append(("sortBy", "DD"))
        elif self.sort_by == "relevant":
            params.append(("sortBy", "R"))

        # keyword/location already '+'-encoded; safe='+' keeps them as-is
        return base + urlencode(params, safe="+")

    # --- fetch single batch ---
    def fetch_job_batch(self, start):
        headers = {
            "User-Agent": get_random_user_agent(),
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.linkedin.com/jobs",
            "X-Requested-With": "XMLHttpRequest",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        resp = requests.get(self.url(start), headers=headers, timeout=10)
        if resp.status_code == 429:
            raise RuntimeError("Rate limit reached")
        if resp.status_code != 200:
            raise RuntimeError(f"Bad status: {resp.status_code}")
        return parse_job_list(resp.text)

    # --- main paginated fetch loop ---
    def get_jobs(self):
        all_jobs = []
        start = 0
        BATCH_SIZE = 25
        consecutive_errors = 0
        MAX_CONSECUTIVE_ERRORS = 3

        logger.info(self.url())
        logger.info(self.get_cache_key())

        cache_key = self.get_cache_key()
        cached = cache.get(cache_key)
        if cached:
            logger.info("Returning cached results")
            return cached

        while True:
            try:
                jobs = self.fetch_job_batch(start)
                if not jobs:
                    break

                all_jobs.extend(jobs)
                logger.info("Fetched %d jobs. Total: %d", len(jobs), len(all_jobs))

                if self.limit and len(all_jobs) >= self.limit:
                    all_jobs = all_jobs[: self.limit]
                    break

                consecutive_errors = 0
                start += BATCH_SIZE
                time.sleep(2 + random.random())  # 2-3s polite delay
            except Exception as error:
                consecutive_errors += 1
                logger.error(
                    "Error fetching batch (attempt %d): %s", consecutive_errors, error
                )
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    logger.info("Max consecutive errors reached. Stopping.")
                    break
                time.sleep(2 ** consecutive_errors)  # exponential backoff

        if all_jobs:
            cache.set(self.get_cache_key(), all_jobs)
        return all_jobs


# --- Parser ---
def _text(node):
    return node.get_text(strip=True) if node else ""


def parse_job_list(job_html):
    jobs = []
    try:
        soup = BeautifulSoup(job_html, "html.parser")
        for li in soup.find_all("li"):
            try:
                position = _text(li.select_one(".base-search-card__title"))
                company = _text(li.select_one(".base-search-card__subtitle"))
                location = _text(li.select_one(".job-search-card__location"))

                date_el = li.find("time")
                date = date_el.get("datetime") if date_el else ""

                salary = _text(li.select_one(".job-search-card__salary-info"))
                salary = " ".join(salary.split())  # collapse whitespace

                link_el = li.select_one(".base-card__full-link")
                job_url = link_el.get("href") if link_el else ""

                logo_el = li.select_one(".artdeco-entity-image")
                company_logo = logo_el.get("data-delayed-url") if logo_el else ""

                ago_time = _text(li.select_one(".job-search-card__listdate"))

                # need at least position + company
                if not position or not company:
                    continue

                jobs.append(
                    {
                        "position": position,
                        "company": company,
                        "location": location,
                        "date": date,
                        "salary": salary or "Not specified",
                        "jobUrl": job_url or "",
                        "companyLogo": company_logo or "",
                        "agoTime": ago_time or "",
                    }
                )
            except Exception as err:
                logger.warning("Error parsing a job card: %s", err)
                continue
    except Exception as error:
        logger.error("Error parsing job list: %s", error)
    return jobs


# --- Public API (mirrors module.exports) ---
def query(query_object):
    return Query(query_object).get_jobs()


def clear_cache():
    cache.clear()


def get_cache_size():
    return cache.size()
