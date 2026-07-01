@echo off
chcp 65001 >nul
setlocal
set PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
set ROOT=%~dp0..
cd /d "%ROOT%\backend"

echo ============================================
echo Expert17025 - Автоматическая настройка
echo ============================================

if not exist "%PY%" (
  echo Python 3.12 не найден. Установите с python.org
  exit /b 1
)

echo [1/5] Скачивание Python-пакетов...
node scripts\download-wheels.mjs
if errorlevel 1 (
  echo Ошибка скачивания wheels
  exit /b 1
)

echo [2/5] Установка Python-пакетов офлайн...
"%PY%" -m pip install --no-index --find-links=wheels -r requirements.txt
if errorlevel 1 (
  echo Повторная попытка без fastembed...
  "%PY%" -m pip install --no-index --find-links=wheels fastapi uvicorn sqlalchemy aiosqlite pydantic pydantic-settings python-jose passlib bcrypt python-multipart pypdf python-docx openpyxl beautifulsoup4 aiofiles email-validator httpx
)

echo [3/5] Инициализация БД и импорт документов...
set PYTHONPATH=%CD%
"%PY%" -m scripts.setup_all

echo [4/5] Установка frontend...
cd /d "%ROOT%\frontend"
call npm install
if errorlevel 1 echo Предупреждение: npm install не удался, frontend можно запустить позже

echo [5/5] Готово!
echo.
echo Backend:  cd backend ^&^& "%PY%" -m uvicorn app.main:app --reload --port 8000
echo Frontend: cd frontend ^&^& npm run dev
echo Вход: admin@expert17025.ru / admin12345
echo ============================================
pause
