# INSTA CLUB Bot

Telegram-бот закрытого сообщества предпринимателей и авторов контента в Сербии.

Стек MVP: **Python + aiogram 3 + SQLite**.  
Позже можно нарастить: PostgreSQL, Redis, платежи, CRM, админку, напоминания.

## Что уже есть

- Главный экран: вступление, о клубе, тарифы, отзывы, куратор
- Онбординг: имя → город → сфера → Instagram → цель
- Главное меню клуба
- Сообщество: представиться, поиск, каталог, новые участники
- База знаний и мероприятия (контент-заготовки)
- Подписка (демо-тариф Business)
- Реферальная ссылка
- Профиль и уведомления
- Базовая админ-команда `/admin`

## Запуск локально

```powershell
cd $env:USERPROFILE\telegram-profile-bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

В `.env`:

```env
BOT_TOKEN=токен_от_BotFather
CURATOR_USERNAME=username_куратора
ADMIN_IDS=ваш_telegram_id
```

```powershell
python -m bot.main
```

В Telegram: `/start`.

## Railway

Variables:

- `BOT_TOKEN`
- `CURATOR_USERNAME`
- `ADMIN_IDS` (через запятую)
- `DB_PATH=/data/profiles.db`

Рекомендуется Volume на `/data`.

После изменений: push в GitHub → Redeploy на Railway.

## Команды

- `/start` — главный экран / меню
- `/menu` — меню участника
- `/cancel` — отмена текущего шага
- `/admin` — статистика (только `ADMIN_IDS`)

## Что специально упрощено

Чтобы не раздувать первую версию:

- SQLite вместо PostgreSQL
- Memory FSM вместо Redis
- Оплата и CRM — заглушки через куратора
- Напоминания и рассылки — следующий этап
- Админка — команда `/admin`, не FastAPI/React
