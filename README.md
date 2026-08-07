# Telegram Profile Bot

Пошаговая анкета профиля на **aiogram 3** с FSM и сохранением в SQLite.

## Требования

- Python 3.10+
- Токен бота от [@BotFather](https://t.me/BotFather)

## Установка и запуск

1. Перейди в папку проекта:

```powershell
cd $env:USERPROFILE\telegram-profile-bot
```

2. Создай виртуальное окружение и установи зависимости:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. Создай файл `.env` из примера и вставь токен:

```powershell
Copy-Item .env.example .env
```

Открой `.env` и укажи:

```env
BOT_TOKEN=123456:ABC-DEF...
```

4. Запусти бота:

```powershell
python -m bot.main
```

5. Открой своего бота в Telegram и отправь `/start`.

## Сценарий

1. `/start` → кнопка «Создать 👨‍💻 Профиль»
2. Имя и фамилия (оставить из Telegram или ввести вручную)
3. Фото
4. Сфера деятельности (inline-кнопки)
5. Описание деятельности
6. Instagram (можно пропустить)
7. Хобби (можно пропустить)
8. Summary + запись в `profiles.db`

## Структура

```text
bot/
  main.py          # точка входа, init БД, polling
  config.py        # токен и путь к БД
  database.py      # SQLite
  states.py        # FSM-состояния
  keyboards.py     # Reply / Inline клавиатуры
  handlers/
    start.py       # /start
    profile.py     # анкета
```

## Деплой на Railway

1. Запушь репозиторий на GitHub.
2. На [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**.
3. Выбери этот репозиторий.
4. В Variables добавь:

```env
BOT_TOKEN=твой_токен_от_BotFather
DB_PATH=/data/profiles.db
```

5. (Рекомендуется) Добавь Volume с mount path `/data`, чтобы SQLite не стиралась при редеплое.
6. Start Command уже задан в `railway.toml`: `python -m bot.main`.
7. После деплоя напиши боту `/start` в Telegram.
