# Выгрузка на GitHub (приватный репозиторий)

Инструкция для ручной загрузки проекта **Expert17025**. В репозиторий попадает только код, без ваших документов и секретов.

## Перед загрузкой — проверьте

| Файл / папка | В репозиторий? |
|--------------|----------------|
| `backend/app/`, `frontend/src/` | Да |
| `.env.example`, `README.md`, `docker-compose.yml` | Да |
| `.env` | **Нет** — API-ключи и пароли |
| `backend/data/*.db` | **Нет** — база с документами |
| `backend/uploads/` | **Нет** — загруженные PDF/DOCX |
| `backend/wheels/` | **Нет** — офлайн-пакеты Python |
| `backend/.venv/`, `node_modules/` | **Нет** |

## Шаг 1. Создайте репозиторий на GitHub

1. Откройте [github.com/new](https://github.com/new)
2. Имя, например: `expert17025`
3. Выберите **Private** (приватный)
4. **Не** ставьте галочки «Add README», «Add .gitignore», «Choose a license» — они уже есть в проекте
5. Нажмите **Create repository**

## Шаг 2. Инициализация git (в папке проекта)

Откройте PowerShell или cmd в папке `ИИ` и выполните:

```powershell
cd "C:\Users\User\OneDrive - Нефтьсервисхолдинг\Рабочий стол\ПРОЕКТЫ ВАЙБ\privat17025\ИИ"

git init
git add .
git status
```

### Обязательная проверка `git status`

В списке **не должно быть**:

- `.env`
- `expert17025.db` (или любые `*.db`)
- папки `backend/uploads/` с файлами
- `backend/wheels/`
- `backend/.venv/`
- `node_modules/`

Если что-то из этого видно — **не делайте commit**, напишите в чат, разберёмся.

## Шаг 3. Первый коммит

```powershell
git commit -m "Initial commit: Expert17025 platform (code only)"
```

## Шаг 4. Привязка к GitHub и загрузка

Подставьте свой логин GitHub вместо `ВАШ_ЛОГИН`:

```powershell
git branch -M main
git remote add origin https://github.com/ВАШ_ЛОГИН/expert17025.git
git push -u origin main
```

При первом push GitHub попросит войти (браузер или Personal Access Token).

### Если репозиторий уже создан с README на GitHub

```powershell
git pull origin main --allow-unrelated-histories
git push -u origin main
```

## Шаг 5. После загрузки

1. В настройках репозитория: **Settings → General → Danger Zone** — убедитесь, что репозиторий **Private**
2. Смените пароль админа после деплоя (по умолчанию в `setup.bat`: `admin@expert17025.ru` / `admin12345`)
3. На сервере создайте свой `.env` из `.env.example`, не копируйте локальный `.env`
4. Базу и документы переносите отдельно (бэкап `expert17025.db` или повторный импорт скриптами)

## Клонирование на другом компьютере

```powershell
git clone https://github.com/ВАШ_ЛОГИН/expert17025.git
cd expert17025
copy .env.example .env
# отредактируйте .env
setup.bat
```

## Бэкап данных (не в Git)

Храните локально или на сервере:

- `backend/data/expert17025.db` — вся база
- `backend/uploads/` — загруженные файлы
- `.env` — секреты

Рекомендуется периодический архив этих трёх элементов отдельно от GitHub.
