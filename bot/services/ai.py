import base64
import json
import re
from typing import Any

from openai import AsyncOpenAI

from bot.config import settings

PHOTO_SYSTEM = """Ты — NutriCoach, AI-нутрициолог в Telegram.
По фото еды оцени калории и БЖУ. Отвечай ТОЛЬКО валидным JSON без markdown:
{
  "description": "краткое название блюда",
  "calories": число,
  "protein_g": число,
  "fat_g": число,
  "carbs_g": число,
  "confidence": "high|medium|low",
  "assumptions": "допущения о порции",
  "tips_good": "что хорошо в этом приёме",
  "tips_limit": "что лучше ограничить (утечки: масло, соусы, порции)"
}
Будь честен с уверенностью. Не давай медицинских диагнозов."""

CHAT_SYSTEM_TEMPLATE = """Ты — NutriCoach, дружелюбный нутрициолог-коуч в Telegram.
Профиль пользователя:
- Пол: {gender}, возраст: {age}
- Рост: {height_cm} см, вес: {weight_kg} кг
- Активность: {activity}
- Цель: {goal} (целевой вес: {target_weight} кг)
- Норма: {calories} ккал, Б{protein}г Ж{fat}г У{carbs}г
- Программа: {program}

Правила:
- Отвечай кратко (до 400 слов), на русском, с эмодзи умеренно
- Давай практичные советы по питанию, не назначай лекарства
- При серьёзных симптомах — рекомендуй врача
- Учитывай цель пользователя"""


def _client() -> AsyncOpenAI | None:
    if not settings.openai_api_key:
        return None
    return AsyncOpenAI(api_key=settings.openai_api_key)


def _parse_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


async def analyze_food_photo(image_bytes: bytes) -> dict[str, Any] | None:
    client = _client()
    if not client:
        return _fallback_photo_analysis()

    b64 = base64.standard_b64encode(image_bytes).decode()
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PHOTO_SYSTEM},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                        },
                        {"type": "text", "text": "Оцени это блюдо."},
                    ],
                },
            ],
            max_tokens=600,
        )
        raw = response.choices[0].message.content or ""
        return _parse_json(raw)
    except Exception:
        return _fallback_photo_analysis()


def _fallback_photo_analysis() -> dict[str, Any]:
    return {
        "description": "Блюдо (оценка без AI)",
        "calories": 350,
        "protein_g": 15,
        "fat_g": 12,
        "carbs_g": 40,
        "confidence": "low",
        "assumptions": "Средняя порция. Добавь OPENAI_API_KEY для точного анализа по фото.",
        "tips_good": "Записывай регулярно — так проще держать дефицит/профицит.",
        "tips_limit": "Уточни порцию и соусы вручную через «Описать еду».",
    }


async def nutrition_chat(user: dict[str, Any], question: str) -> str:
    client = _client()
    if not client:
        return _fallback_chat_response(question, user)

    from bot.services.nutrition import ACTIVITY_LABELS, GOAL_LABELS

    system = CHAT_SYSTEM_TEMPLATE.format(
        gender="жен" if user.get("gender") == "female" else "муж",
        age=user.get("age", "?"),
        height_cm=user.get("height_cm", "?"),
        weight_kg=user.get("weight_kg", "?"),
        activity=ACTIVITY_LABELS.get(user.get("activity", ""), user.get("activity", "?")),
        goal=GOAL_LABELS.get(user.get("goal", ""), user.get("goal", "?")),
        target_weight=user.get("target_weight_kg", "—"),
        calories=user.get("daily_calories", "?"),
        protein=user.get("daily_protein_g", "?"),
        fat=user.get("daily_fat_g", "?"),
        carbs=user.get("daily_carbs_g", "?"),
        program=user.get("program", "maintain"),
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": question},
            ],
            max_tokens=800,
        )
        return response.choices[0].message.content or "Не удалось получить ответ."
    except Exception as e:
        return f"⚠️ Ошибка AI: {e}\n\nПопробуй позже."


def _fallback_chat_response(question: str, user: dict) -> str:
    q = question.lower()
    cal = user.get("daily_calories", 2000)
    if "белк" in q or "протеин" in q:
        return (
            f"🥩 Рекомендуемый белок: ~{user.get('daily_protein_g', 100)} г/день.\n"
            "Источники: курица, рыба, творог, яйца, бобовые."
        )
    if "похуд" in q or "дефицит" in q:
        return (
            f"🎯 Твоя норма: {cal} ккал/день.\n"
            "Держи дефицит 300–500 ккал, следи за белком и записывай «утечки» "
            "(масло, соусы, напитки)."
        )
    return (
        "💡 Для персональных AI-ответов добавь OPENAI_API_KEY в .env\n\n"
        f"Твоя норма: {cal} ккал. Задай конкретный вопрос про питание, "
        "меню или перекусы."
    )
