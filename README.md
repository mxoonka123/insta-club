# INSTA CLUB Bot

Telegram-бот закрытого сообщества предпринимателей и авторов контента в Сербии.

Стек MVP: **Python + aiogram 3 + SQLite**.  
Позже можно нарастить: PostgreSQL, Redis, платежи, CRM, админку, напоминания.

## Что уже есть

- Главный экран: вступление, о клубе, тарифы, отзывы, куратор
- Онбординг и заявка в клуб
- Статусы: заявка → оплата на проверке → активный участник
- Кнопка «Я оплатил» + уведомление админам
- Одобрение / отклонение заявки админом
- Главное меню клуба после одобрения
- Сообщество, каталог, база знаний, мероприятия
- Подписка и продление через куратора
- Реферальная ссылка
- Профиль и уведомления

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
BUSINESS_PRICE=9 900 RSD / месяц
PAYMENT_DETAILS=Как оплатить и куда писать после оплаты
```

```powershell
python -m bot.main
```

В Telegram: `/start`.

## Railway

Variables:

- `BOT_TOKEN`
- `CURATOR_USERNAME`
- `ADMIN_IDS` (через запятую, обязательно для одобрения заявок)
- `BUSINESS_PRICE`
- `PAYMENT_DETAILS`
- `DB_PATH=/data/profiles.db`

Рекомендуется Volume на `/data`.

После изменений: push в GitHub → Redeploy на Railway.

## Команды

- `/start` — главный экран / меню
- `/menu` — меню участника
- `/cancel` — отмена текущего шага
- `/admin` — статистика
- `/applications` — заявки на проверке
- `/find имя` — найти участника
- `/approve ID` — одобрить участника
- `/reject ID` — отклонить заявку
- `/kick ID` — закрыть доступ уже одобренному
- `/renew ID` — продлить подписку на 30 дней
- `/meeting` — создать клубную встречу

## Сценарий для демо

1. Новый пользователь: `/start` → «Стать участником» → анкета  
2. Видит тариф и кнопку «Я оплатил»  
3. Админ получает заявку → «Одобрить»  
4. Пользователю открывается меню клуба  
5. Показать каталог, мероприятие, базу знаний  

## Что специально упрощено

- SQLite вместо PostgreSQL
- Memory FSM вместо Redis
- Оплата вручную через куратора (без Stripe)
- Напоминания и рассылки — следующий этап
- Админка в Telegram-командах, не FastAPI/React
