@echo off
setlocal enabledelayedexpansion

set "PY_CMD=py"
where py >nul 2>nul || set "PY_CMD=python"

REM Load .env file if exists
if exist "backend\.env" (
  for /f "usebackq tokens=1,* delims==" %%A in (`findstr /v "^#" backend\.env`) do (
    set "%%A=%%B"
  )
)


echo Installing backend deps...
cd backend
%PY_CMD% -m pip install -q -r requirements.txt
cd ..

echo Installing frontend deps...
cd frontend
call npm install -q 2>nul || call npm install
cd ..

echo Starting backend...
cd backend
start "Dattack Backend" cmd /k "%PY_CMD% -m uvicorn main:app --reload --port 8000"
cd ..

echo Starting frontend...
cd frontend
start "Dattack Frontend" cmd /k "npm run dev"
cd ..

echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Close the terminal windows to stop
