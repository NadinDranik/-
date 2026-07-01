@echo off
chcp 65001 >nul
set PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
cd /d "%~dp0backend"
set PYTHONPATH=%CD%
start "Expert17025 API" "%PY%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
cd /d "%~dp0frontend"
if exist node_modules (
  start "Expert17025 Web" cmd /c "npm run dev"
) else (
  echo Frontend: сначала выполните npm install в папке frontend
)
echo.
echo Backend:  http://localhost:8000
echo Swagger:  http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo Вход: admin@expert17025.ru / admin12345
pause
