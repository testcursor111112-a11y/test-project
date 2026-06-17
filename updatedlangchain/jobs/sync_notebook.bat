@echo off
echo ===================================================
echo Syncing Jupyter Notebooks to Python scripts...
echo ===================================================

echo 1. Syncing job_finder_agent.ipynb ...
"c:\Users\FRONTECH\Desktop\test-project\.venv\Scripts\python.exe" -m jupyter nbconvert --to script "c:\Users\FRONTECH\Desktop\test-project\updatedlangchain\jobs\job_finder_agent.ipynb"
set JOB_FINDER_ERR=%ERRORLEVEL%

echo 2. Syncing company_contract_mailer_zoho.ipynb ...
"c:\Users\FRONTECH\Desktop\test-project\.venv\Scripts\python.exe" -m jupyter nbconvert --to script "c:\Users\FRONTECH\Desktop\test-project\updatedlangchain\jobs\company_contract_mailer_zoho.ipynb"
set MAILER_ERR=%ERRORLEVEL%

echo ===================================================
if %JOB_FINDER_ERR% equ 0 (
    echo [SUCCESS] job_finder_agent.ipynb synced successfully.
) else (
    echo [ERROR] Failed to sync job_finder_agent.ipynb.
)

if %MAILER_ERR% equ 0 (
    echo [SUCCESS] company_contract_mailer_zoho.ipynb synced successfully.
) else (
    echo [ERROR] Failed to sync company_contract_mailer_zoho.ipynb.
)
echo ===================================================
pause
