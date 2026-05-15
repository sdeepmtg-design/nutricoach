"""Расчёт норм КБЖУ по профилю пользователя (формула Mifflin-St Jeor)."""

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

GOAL_ADJUSTMENTS = {
    "lose": -0.15,
    "maintain": 0.0,
    "gain": 0.10,
}

GOAL_LABELS = {
    "lose": "Похудение",
    "maintain": "Поддержание веса",
    "gain": "Набор массы",
}

ACTIVITY_LABELS = {
    "sedentary": "Сидячий образ жизни",
    "light": "Лёгкая активность (1–3 трен./нед)",
    "moderate": "Умеренная (3–5 трен./нед)",
    "active": "Высокая (6–7 трен./нед)",
    "very_active": "Очень высокая (физ. работа + спорт)",
}


def bmr(gender: str, weight_kg: float, height_cm: float, age: int) -> float:
    if gender == "female":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5


def calculate_targets(
    gender: str,
    age: int,
    height_cm: float,
    weight_kg: float,
    activity: str,
    goal: str,
) -> dict[str, int]:
    base = bmr(gender, weight_kg, height_cm, age)
    multiplier = ACTIVITY_MULTIPLIERS.get(activity, 1.375)
    tdee = base * multiplier
    adjustment = GOAL_ADJUSTMENTS.get(goal, 0.0)
    calories = int(round(tdee * (1 + adjustment)))

    # Макросы: белок 1.8 г/кг, жиры 25%, остальное — углеводы
    protein_g = int(round(weight_kg * 1.8))
    fat_g = int(round(calories * 0.25 / 9))
    protein_cal = protein_g * 4
    fat_cal = fat_g * 9
    carbs_g = max(0, int(round((calories - protein_cal - fat_cal) / 4)))

    return {
        "daily_calories": calories,
        "daily_protein_g": protein_g,
        "daily_fat_g": fat_g,
        "daily_carbs_g": carbs_g,
    }


def day_summary(meals: list[dict], targets: dict[str, int]) -> str:
    eaten_cal = sum(m.get("calories", 0) for m in meals)
    eaten_p = sum(m.get("protein_g", 0) for m in meals)
    eaten_f = sum(m.get("fat_g", 0) for m in meals)
    eaten_c = sum(m.get("carbs_g", 0) for m in meals)

    cal_target = targets.get("daily_calories", 0)
    remaining = cal_target - eaten_cal
    pct = int(eaten_cal / cal_target * 100) if cal_target else 0

    bar_filled = min(10, pct // 10)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)

    status = "в норме ✅"
    if remaining < -200:
        status = "перебор ⚠️"
    elif remaining > 400:
        status = "ещё можно поесть 🍽"

    lines = [
        f"📊 <b>План на сегодня</b>",
        f"",
        f"Калории: {bar} {pct}%",
        f"Съедено: <b>{eaten_cal}</b> / {cal_target} ккал",
        f"Осталось: <b>{remaining}</b> ккал — {status}",
        f"",
        f"Б: {eaten_p:.0f}/{targets.get('daily_protein_g', 0)} г",
        f"Ж: {eaten_f:.0f}/{targets.get('daily_fat_g', 0)} г",
        f"У: {eaten_c:.0f}/{targets.get('daily_carbs_g', 0)} г",
    ]

    if meals:
        lines.append("")
        lines.append("<b>Приёмы пищи:</b>")
        for m in meals:
            mt = m.get("meal_type", "meal")
            icon = {"breakfast": "🌅", "lunch": "☀️", "dinner": "🌙", "snack": "🍎"}.get(mt, "🍽")
            lines.append(
                f"{icon} {m.get('description', '')[:40]} — {m.get('calories', 0)} ккал"
            )
    else:
        lines.append("")
        lines.append("<i>Пока нет записей. Отправь фото еды или опиши приём пищи.</i>")

    return "\n".join(lines)


def week_insights(meals: list[dict], user: dict) -> str:
    if not meals:
        return "📈 <b>Итоги недели</b>\n\nНедостаточно данных. Записывай приёмы пищи каждый день!"

    total_cal = sum(m.get("calories", 0) for m in meals)
    days_with_meals = len({m["created_at"][:10] for m in meals})
    avg_cal = total_cal // max(days_with_meals, 1)
    target = user.get("daily_calories", 2000)

    high_cal_meals = sorted(meals, key=lambda x: x.get("calories", 0), reverse=True)[:3]

    goal = user.get("goal", "maintain")
    tips = []
    if goal == "lose" and avg_cal > target:
        tips.append("• Средняя калорийность выше цели — проверь «утечки» (соусы, напитки, порции)")
    elif goal == "gain" and avg_cal < target:
        tips.append("• Калорий меньше цели — добавь перекусы с белком и сложными углеводами")
    if days_with_meals < 5:
        tips.append("• Записывай еду чаще — точность плана растёт с регулярностью")

    lines = [
        "📈 <b>Итоги недели</b>",
        "",
        f"Дней с записями: <b>{days_with_meals}/7</b>",
        f"Средняя калорийность: <b>{avg_cal}</b> ккал/день (цель: {target})",
        "",
        "<b>Самые калорийные приёмы:</b>",
    ]
    for m in high_cal_meals:
        lines.append(f"• {m.get('description', '')[:35]} — {m.get('calories', 0)} ккал")

    if tips:
        lines.extend(["", "<b>Фокус на следующую неделю:</b>", *tips])
    else:
        lines.extend(["", "✅ Хорошая динамика! Продолжай в том же духе."])

    return "\n".join(lines)
