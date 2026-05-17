@echo off
REM Check if poster is already running
tasklist /fi "imagename eq pythonw.exe" 2>NUL | find /I "pythonw.exe" >NUL
if "%ERRORLEVEL%"=="0" (
    echo Poster already running
    exit /b
)

echo Starting poster + watchdog...
cd /d C:\Users\vince\wagmi-project
start /B pythonw -u bluestacks_poster.py > bluestacks_poster_output.log 2>&1
timeout /t 2 /nobreak >NUL
start /B pythonw -u watchdog.py > watchdog_output.log 2>&1
echo Started
