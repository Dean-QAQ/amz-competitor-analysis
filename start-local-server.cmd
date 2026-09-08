@echo off
cd /d "%~dp0"
echo [%date% %time%] starting local server>> "server-run.log"
where node >nul 2>nul
if %errorlevel%==0 (
  echo using PATH node>> "server-run.log"
  node ".local_static_server.js" >> "server-run.log" 2>> "server-run.err.log"
  echo [%date% %time%] exited %errorlevel%>> "server-run.log"
  exit /b %errorlevel%
)
echo Node.js not found. Please install Node.js or add node.exe to PATH.>> "server-run.err.log"
pause
