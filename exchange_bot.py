import os
from typing import Dict

import requests
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")

if not BOT_TOKEN or not API_KEY:
    raise ValueError("Не удалось загрузить BOT_TOKEN или API_KEY. Проверьте файл .env.")

BASE_URLS = {
    "RUB": f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/RUB",
    "USD": f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD",
    "EUR": f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/EUR",
    "CNY": f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/CNY",
}

CURRENCIES = ("RUB", "USD", "EUR", "CNY")


def _format_rate(rate: float) -> str:
    return f"{rate:.4f}" if isinstance(rate, (int, float)) else "недоступно"


def build_main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🇷🇺 RUB", callback_data="base:RUB"),
            InlineKeyboardButton("🇺🇸 USD", callback_data="base:USD"),
        ],
        [
            InlineKeyboardButton("🇪🇺 EUR", callback_data="base:EUR"),
            InlineKeyboardButton("🇨🇳 CNY", callback_data="base:CNY"),
        ],
        [InlineKeyboardButton("🔄 Обновить курсы", callback_data="refresh_rates")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_target_menu(base: str) -> InlineKeyboardMarkup:
    buttons = []
    for target in CURRENCIES:
        if target == base:
            continue
        buttons.append([InlineKeyboardButton(target, callback_data=f"target:{base}:{target}")])
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="back:main")])
    return InlineKeyboardMarkup(buttons)


def build_amount_keyboard(base: str, target: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⬅️ Выбрать другую валюту", callback_data=f"base:{base}")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back:main")],
        ]
    )


def build_result_keyboard(base: str, target: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔁 Повторить", callback_data=f"target:{base}:{target}")],
            [InlineKeyboardButton("⬅️ Назад", callback_data=f"base:{base}")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back:main")],
        ]
    )


def format_rates_summary(rates: Dict[str, Dict[str, float]]) -> str:
    lines = []
    for base in CURRENCIES:
        conversions = []
        for target in CURRENCIES:
            if target == base:
                continue
            rate = rates.get(base, {}).get(target)
            conversions.append(f"{target}: {_format_rate(rate)}")
        base_line = f"1 {base} → " + " | ".join(conversions)
        lines.append(base_line)
    return "\n".join(lines)


async def fetch_exchange_rates() -> Dict[str, Dict[str, float]]:
    rates: Dict[str, Dict[str, float]] = {}
    for base, url in BASE_URLS.items():
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            conversions = {}
            for target in CURRENCIES:
                if target == base:
                    continue
                conversions[target] = data["conversion_rates"].get(target)
            rates[base] = conversions
        except Exception as exc:  # noqa: BLE001
            print(f"Ошибка при получении курсов валют для {base}: {exc}")
            rates[base] = {target: None for target in CURRENCIES if target != base}
    return rates


async def ensure_rates(context: ContextTypes.DEFAULT_TYPE, force_refresh: bool = False) -> Dict[str, Dict[str, float]]:
    if force_refresh or "rates" not in context.user_data:
        context.user_data["rates"] = await fetch_exchange_rates()
    return context.user_data["rates"]


def build_welcome_message(rates: Dict[str, Dict[str, float]], *, refreshed: bool = False) -> str:
    header = [
        "✨ Добро пожаловать в конвертер валют!",
        "Здесь вы мгновенно узнаете актуальные курсы и можете конвертировать нужную сумму.",
    ]
    if refreshed:
        header.append("✅ Курсы только что обновлены.")

    rates_block = [
        "\n📊 Актуальные курсы:",
        "━━━━━━━━━━━━━━━━━━━━━━",
        format_rates_summary(rates),
        "━━━━━━━━━━━━━━━━━━━━━━",
    ]

    menu_hint = [
        "\n📋 Меню действий:",
        "• Нажмите на валюту, чтобы выбрать базовую.",
        "• После выбора укажите валюту назначения и введите сумму.",
        "• Используйте кнопку 🔄, чтобы обновить данные в любой момент.",
    ]

    return "\n".join(header + rates_block + menu_hint)


async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, *, refreshed: bool = False) -> None:
    rates = await ensure_rates(context, force_refresh=refreshed)
    message = build_welcome_message(rates, refreshed=refreshed)
    reply_markup = build_main_menu()

    if update.message:
        await update.message.reply_text(message, reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(message, reply_markup=reply_markup)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_main_menu(update, context)


async def refresh_rates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_main_menu(update, context, refreshed=True)


async def select_base_currency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    base = query.data.split(":")[1]
    context.user_data["selected_base"] = base
    rates = await ensure_rates(context)
    if base not in rates:
        await query.edit_message_text("Курсы для выбранной валюты недоступны. Попробуйте обновить.", reply_markup=build_main_menu())
        return

    keyboard = build_target_menu(base)
    await query.edit_message_text(
        text=f"Выберите валюту, в которую хотите конвертировать {base}:",
        reply_markup=keyboard,
    )


async def select_target_currency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, base, target = query.data.split(":")
    context.user_data["conversion"] = {"base": base, "target": target}

    await query.edit_message_text(
        text=(
            f"Введите сумму в {base}, чтобы конвертировать в {target}.\n"
            "Отправьте число сообщением."
        ),
        reply_markup=build_amount_keyboard(base, target),
    )


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_main_menu(update, context)


async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conversion = context.user_data.get("conversion")
    rates = context.user_data.get("rates")

    if not conversion or not rates:
        await update.message.reply_text("Сначала выберите направление конвертации через меню.")
        return

    base = conversion["base"]
    target = conversion["target"]
    rate = rates.get(base, {}).get(target)

    if rate in (None, 0):
        await update.message.reply_text(
            "Курс недоступен. Обновите данные и попробуйте снова.",
            reply_markup=build_main_menu(),
        )
        return

    try:
        amount = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число.")
        return

    result = amount * rate
    message = f"{amount:.2f} {base} = {result:.2f} {target}"

    await update.message.reply_text(message, reply_markup=build_result_keyboard(base, target))


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"Произошла ошибка: {context.error}")


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(refresh_rates, pattern="^refresh_rates$"))
    application.add_handler(CallbackQueryHandler(select_base_currency, pattern=r"^base:(RUB|USD|EUR|CNY)$"))
    application.add_handler(
        CallbackQueryHandler(
            select_target_currency,
            pattern=r"^target:(RUB|USD|EUR|CNY):(RUB|USD|EUR|CNY)$",
        )
    )
    application.add_handler(CallbackQueryHandler(back_to_main, pattern="^back:main$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount))
    application.add_error_handler(error_handler)

    application.run_polling()


if __name__ == "__main__":
    main()
