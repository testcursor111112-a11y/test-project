# Job Automation Documentation

This document records the configuration and automation of the **Job Finder Agent** and the **Company Contract Mailer** scripts on Windows.

---

## 1. Summary of Automated Jobs

### Job 1: Job Finder Agent
* **Purpose**: Fetches remote job postings for MERN/Fullstack/Backend roles from the JSearch API, dedupes them against the Google Sheet, filters relevant items using Gemini, and logs the results in Google Sheets + emails a summary CSV to the BDE.
* **Scheduled Time**: Every weekday (Monday through Friday) at **9:00 AM**.
* **Task Name**: `JobFinderAgent`
* **Script File**: [job_finder_agent.py](file:///c:/Users/FRONTECH/Desktop/test-project/updatedlangchain/jobs/job_finder_agent.py)

### Job 2: Company Contract Mailer
* **Purpose**: Processes job rows in Google Sheets pending outreach (Contact Email exists but no Contract Mail Sent stamp). It researches target companies via DuckDuckGo, selects the best matching available candidate profiles, drafts custom outreach mail using Gemini, and sends outreach via Zoho SMTP (attaching direct-download resume PDFs).
* **Scheduled Time**: Every weekday (Monday through Friday) at **11:00 AM**.
* **Task Name**: `CompanyContractMailer`
* **Script File**: [company_contract_mailer_zoho.py](file:///c:/Users/FRONTECH/Desktop/test-project/updatedlangchain/jobs/company_contract_mailer_zoho.py)

---

## 2. Shared File Structure

* **[job_finder_agent.ipynb](file:///c:/Users/FRONTECH/Desktop/test-project/updatedlangchain/jobs/job_finder_agent.ipynb)** (Updated JSearch helper with exponential backoff retry logic and exception handling).
* **[company_contract_mailer_zoho.ipynb](file:///c:/Users/FRONTECH/Desktop/test-project/updatedlangchain/jobs/company_contract_mailer_zoho.ipynb)** (Updated setup and previews path resolution for system execution safety).
* **[sync_notebook.bat](file:///c:/Users/FRONTECH/Desktop/test-project/updatedlangchain/jobs/sync_notebook.bat)** (Single batch file to compile/sync both Jupyter notebooks to python script formats).
* **[.env](file:///c:/Users/FRONTECH/Desktop/test-project/.env)** (Updated path separators in `SERVICE_ACCOUNT_PATH` to forward-slashes to prevent backslash parsing errors in Python).

---

## 3. How to Update the Codes (Jupyter Syncing)

Because the Windows Task Scheduler runs standalone Python files (`.py`), editing code inside the Jupyter Notebooks (`.ipynb`) will **not** automatically apply changes to the scheduler.

Whenever you update the code inside the notebooks:
1. Double-click the **[sync_notebook.bat](file:///c:/Users/FRONTECH/Desktop/test-project/updatedlangchain/jobs/sync_notebook.bat)** script in your `jobs/` directory.
2. It will compile both notebooks into their Python formats, immediately updating the scheduler's target files.

*(Alternative CLI commands)*:
```cmd
c:\Users\FRONTECH\Desktop\test-project\.venv\Scripts\python -m jupyter nbconvert --to script c:\Users\FRONTECH\Desktop\test-project\updatedlangchain\jobs\job_finder_agent.ipynb
c:\Users\FRONTECH\Desktop\test-project\.venv\Scripts\python -m jupyter nbconvert --to script c:\Users\FRONTECH\Desktop\test-project\updatedlangchain\jobs\company_contract_mailer_zoho.ipynb
```

---

## 4. Command Reference for Scheduled Tasks

You can control both scheduled tasks directly from your terminal using `schtasks`:

### Check Task Status
To view current state, next run time, and parameters:
* **Job Finder Agent**:
  ```cmd
  schtasks /query /tn "JobFinderAgent" /fo list /v
  ```
* **Company Contract Mailer**:
  ```cmd
  schtasks /query /tn "CompanyContractMailer" /fo list /v
  ```

### Run Tasks Manually (For Testing)
To trigger immediate background runs:
* **Job Finder Agent**:
  ```cmd
  schtasks /run /tn "JobFinderAgent"
  ```
* **Company Contract Mailer**:
  ```cmd
  schtasks /run /tn "CompanyContractMailer"
  ```

### Stop Tasks (If Frozen / Running Too Long)
To force terminate a background task execution:
* **Job Finder Agent**:
  ```cmd
  schtasks /end /tn "JobFinderAgent"
  ```
* **Company Contract Mailer**:
  ```cmd
  schtasks /end /tn "CompanyContractMailer"
  ```

### Delete / Remove Tasks
To uninstall the tasks from Windows Task Scheduler:
* **Job Finder Agent**:
  ```cmd
  schtasks /delete /tn "JobFinderAgent" /f
  ```
* **Company Contract Mailer**:
  ```cmd
  schtasks /delete /tn "CompanyContractMailer" /f
  ```

---

## 5. Behavior on PC Restarts and Missed Runs

* **Requires User Logon**: Since the tasks run under your user profile (`FRONTECH`), the computer must be powered on and you must be logged into Windows for them to execute.
* **Handling Missed Runs (Start When Available)**: Both tasks have been configured with the `StartWhenAvailable` setting enabled. If your PC is shut down or asleep during a scheduled execution time (e.g., your PC is off at 9:00 AM and you turn it on at 9:30 AM), Windows Task Scheduler will detect the missed run and **execute the task automatically as soon as the PC boots and you log in**.

