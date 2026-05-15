# NutriCoach — Telegram-бот нутрициолога

AI-бот для подсчёта калорий по фото, дневника питания и монетизации через **Telegram Stars**.

## Конкурентный анализ

| Бот | Free | Pro цена | Сильные стороны |
|-----|------|----------|-----------------|
| [NutriAI](https://nutri-ai.app/) | 3 фото/день, 30/мес | 199₽/мес | Быстрый анализ фото, «утечки» |
| [Nutrition AI](https://nutrition-online.com/) | ограниченно | 490₽/мес | Программы питания |
| [Nutribot](https://nutri-bot.ru/) | демо | от 490₽/мес | AI 24/7 |

**NutriCoach** — между NutriAI и Nutrition AI:
- Free: 3 фото/день + 5 AI-вопросов (как у лидеров)
- Pro через Stars (без ЮKassa) — дневник, неделя, вес, программы
- Честная уверенность анализа + подсказки «хорошо / ограничить»

## Запуск локально

```bash
cd nutricoach-bot
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env
# Заполни BOT_TOKEN и OPENAI_API_KEY
python main.py
```

## Деплой на Render (Web Service)

Бот работает через **webhook** — Render сам подставляет `RENDER_EXTERNAL_URL`, вручную `WEBHOOK_URL` указывать не нужно.

1. Залей репозиторий на GitHub (без `.env` — он в `.gitignore`).
2. [dashboard.render.com](https://dashboard.render.com) → **New** → **Blueprint** → репозиторий.
3. Render подхватит `render.yaml` (тип **Web Service**, план free).
4. В Environment задай `BOT_TOKEN`, `OPENAI_API_KEY`, при желании `ADMIN_IDS`.
5. **Deploy** — в логах: `NutriCoach webhook: https://.../webhook`.

Проверка: открой `https://твой-сервис.onrender.com/health` — должно быть `ok`.

> **Важно:** на бесплатном тарифе сервис засыпает без трафика (~15 мин), SQLite сбрасывается при перезапуске. Для 24/7 — план Starter или cron-пинг `/health`.

## Переменные (.env)

- `BOT_TOKEN` — от [@BotFather](https://t.me/BotFather)
- `OPENAI_API_KEY` — для анализа фото и чата (без ключа — базовые ответы)
- `PRO_MONTH_STARS` / `PRO_YEAR_STARS` — цена в Telegram Stars

## Монетизация

1. В [@BotFather](https://t.me/BotFather) включи **Payments** → Telegram Stars
2. Пользователь нажимает «⭐ Pro» → оплата XTR
3. После `successful_payment` активируется Pro на 30/365 дней

## Команды

- `/start` — онбординг и меню
- `/menu` — главное меню

## Структура

```
nutricoach-bot/
  main.py
  bot/
    handlers/   # start, onboarding, menu, photo, meal, chat, payment
    services/   # nutrition, ai, limits
    database/   # SQLite
    keyboards/
```
