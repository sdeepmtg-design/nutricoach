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

## Деплой на Render

### Вариант A — Worker (рекомендуется, polling)

Стабильно работает 24/7. Нужен план **Starter** (~$7/мес).

1. Залей репозиторий на GitHub (без `.env` — он в `.gitignore`).
2. [dashboard.render.com](https://dashboard.render.com) → **New** → **Blueprint** → репозиторий.
3. Render подхватит `render.yaml`.
4. В Environment задай `BOT_TOKEN`, `OPENAI_API_KEY`, при желании `ADMIN_IDS`.
5. **Deploy** — в логах: `NutriCoach polling started`.

### Вариант B — Web + webhook (бесплатно)

1. Переименуй `render.web.yaml` → `render.yaml` (или создай Web Service вручную).
2. Start command: `python main.py`, Build: `pip install -r requirements.txt`.
3. После первого деплоя скопируй URL сервиса (например `https://nutricoach-bot.onrender.com`).
4. Добавь переменную `WEBHOOK_URL=https://nutricoach-bot.onrender.com` и передеплой.
5. `BOT_MODE=webhook` уже в конфиге.

> **Важно:** на бесплатном тарифе диск эфемерный — SQLite сбросится при перезапуске. Для продакшена подключи Render Disk или внешнюю БД.

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
