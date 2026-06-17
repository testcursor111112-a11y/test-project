@echo off
echo Syncing job_finder_agent.ipynb to job_finder_agent.py...
"c:\Users\FRONTECH\Desktop\test-project\.venv\Scripts\python.exe" -m jupyter nbconvert --to script "c:\Users\FRONTECH\Desktop\test-project\updatedlangchain\jobs\job_finder_agent.ipynb"
if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] Notebook synced successfully. The scheduled task will use the updated code.
) else (
    echo [ERROR] Failed to sync notebook. Please check your notebook file.
)
pause
