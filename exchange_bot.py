import os
from datetime import datetime
from typing import Optional
import xml.etree.ElementTree as ET

import requests
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение токенов
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("Не удалось загрузить BOT_TOKEN. Проверьте файл .env.")

CBR_URL = "https://www.cbr.ru/scripts/XML_daily.asp"
FOREIGN_CURRENCIES = ("USD", "EUR", "CNY")
ALL_CURRENCIES = ("RUB",) + FOREIGN_CURRENCIES

CURRENCY_LABELS = {
    "RUB": "🇷🇺 RUB",
    "USD": "🇺🇸 USD",
    "EUR": "🇪🇺 EUR",
    "CNY": "🇨🇳 CNY",
}

PERSISTENT_MENU = ReplyKeyboardMarkup(
    [["🏠 Меню", "💱 Конвертация"], ["📅 Выбрать дату"]],
    resize_keyboard=True,
)

MENU_KEYWORDS = {"/start", "меню", "menu", "🏠 меню", "🏠", "главное меню"}
CONVERT_KEYWORDS = {"конвертация", "конвертировать", "💱 конвертация"}
DATE_KEYWORDS = {"дата", "📅 выбрать дату", "выбрать дату"}


def _parse_cbr_response(content: str):
    """Преобразовать XML с сайта ЦБ РФ в словарь курсов."""
    root = ET.fromstring(content)
    rates = {"RUB": 1.0}

    for valute in root.findall("Valute"):
        char_code = valute.find("CharCode").text
        nominal = float(valute.find("Nominal").text.replace(",", "."))
        value = float(valute.find("Value").text.replace(",", "."))
        rate = value / nominal  # Стоимость одной единицы валюты в рублях
        rates[char_code] = rate

    # Атрибут Date уже в формате ДД.ММ.ГГГГ
    return rates, root.attrib.get("Date")


async def fetch_exchange_rates(date: Optional[datetime] = None):
    """Получить курсы валют ЦБ РФ для указанной даты."""
    params = {}
    if date:
        params["date_req"] = date.strftime("%d/%m/%Y")

    try:
        response = requests.get(CBR_URL, params=params, timeout=10)
        response.raise_for_status()
        rates, response_date = _parse_cbr_response(response.text)
        return rates, response_date
    except Exception as e:
        print(f"Ошибка при получении курсов валют: {e}")
        fallback_rates = {code: None for code in FOREIGN_CURRENCIES}
        fallback_rates["RUB"] = 1.0
        return fallback_rates, None
    

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Точка входа — показывает главное меню с актуальными курсами."""
    context.user_data['awaiting_date'] = False
    context.user_data['awaiting_amount'] = False
    await show_main_menu(update, context)

async def show_main_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    info_message: Optional[str] = None,
):
    """Показать главное меню с актуальными курсами и кнопками навигации."""

    selected_date = context.user_data.get('selected_date')
    if not selected_date:
        selected_date = datetime.now()
        context.user_data['selected_date'] = selected_date

    rates, response_date = await fetch_exchange_rates(selected_date)
    context.user_data['rates'] = rates
    context.user_data['response_date'] = response_date

    lines = [
        f"Курсы ЦБ РФ на {response_date or selected_date.strftime('%d.%m.%Y')}:"
    ]
    for code in FOREIGN_CURRENCIES:
        value = rates.get(code)
        formatted = "н/д" if value in (None, 0) else f"{value:.4f}"
        lines.append(f"1 {code} = {formatted} RUB")

    message = "\n".join(lines)
    if info_message:
        message = f"{info_message}\n\n{message}"

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💱 Конвертация", callback_data="convert_menu")],
            [InlineKeyboardButton("📅 Выбрать дату", callback_data="change_date")],
        ]
    )

    if update.message:
        await update.message.reply_text(message, reply_markup=keyboard)
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(message, reply_markup=keyboard)

    await _ensure_reply_keyboard(update, context)


async def _ensure_reply_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить reply-клавиатуру один раз, чтобы не использовать /start."""
    if context.user_data.get('reply_keyboard_sent'):
        return

    chat = update.effective_chat
    if not chat:
        return

    context.user_data['reply_keyboard_sent'] = True
    await context.bot.send_message(
        chat_id=chat.id,
        text="Быстрые действия доступны на клавиатуре ниже.",
        reply_markup=PERSISTENT_MENU,
    )


async def open_conversion_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Первый шаг конвертации — выбор базовой валюты."""
    context.user_data['awaiting_amount'] = False
    context.user_data.pop('base_currency', None)
    context.user_data.pop('target_currency', None)

    keyboard = _build_base_currency_keyboard()
    text = "Выберите валюту, из которой будем конвертировать:"

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)


def _build_base_currency_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(CURRENCY_LABELS["RUB"], callback_data="base:RUB"),
         InlineKeyboardButton(CURRENCY_LABELS["USD"], callback_data="base:USD")],
        [InlineKeyboardButton(CURRENCY_LABELS["EUR"], callback_data="base:EUR"),
         InlineKeyboardButton(CURRENCY_LABELS["CNY"], callback_data="base:CNY")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(rows)


async def select_base_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранить выбранную базовую валюту и показать список доступных целей."""
    query = update.callback_query
    await query.answer()

    base_currency = query.data.split(":", maxsplit=1)[1]
    context.user_data['base_currency'] = base_currency

    keyboard = _build_target_currency_keyboard(base_currency)
    await query.edit_message_text(
        text=f"Вы выбрали {CURRENCY_LABELS[base_currency]}. Теперь выберите валюту назначения:",
        reply_markup=keyboard,
    )


def _build_target_currency_keyboard(base_currency: str) -> InlineKeyboardMarkup:
    rows = []
    for target in ALL_CURRENCIES:
        if target == base_currency:
            continue
        label = f"{CURRENCY_LABELS[base_currency]} → {CURRENCY_LABELS[target]}"
        rows.append([InlineKeyboardButton(label, callback_data=f"target:{target}")])

    rows.append([InlineKeyboardButton("🔁 Сменить базовую валюту", callback_data="convert_menu")])
    rows.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(rows)


async def select_target_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Финальный шаг перед вводом суммы — сохранение валюты назначения."""
    query = update.callback_query
    await query.answer()

    base_currency = context.user_data.get('base_currency')
    if not base_currency:
        await query.edit_message_text(
            "Сначала выберите базовую валюту.",
            reply_markup=_build_base_currency_keyboard(),
        )
        return

    target_currency = query.data.split(":", maxsplit=1)[1]
    context.user_data['target_currency'] = target_currency
    context.user_data['awaiting_amount'] = True

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔁 Выбрать другую пару", callback_data="convert_menu")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
        ]
    )

    await query.edit_message_text(
        text=(
            f"Введите сумму в {CURRENCY_LABELS[base_currency]},\n"
            f"чтобы получить результат в {CURRENCY_LABELS[target_currency]}"
        ),
        reply_markup=keyboard,
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка произвольного текста — дата, сумма или команды меню."""
    text = update.message.text.strip()
    normalized = text.lower()

    if context.user_data.get('awaiting_date'):
        await _handle_date_input(update, context)
        return

    if context.user_data.get('awaiting_amount'):
        await _handle_amount_input(update, context)
        return

    if normalized in MENU_KEYWORDS:
        await show_main_menu(update, context)
        return

    if normalized in CONVERT_KEYWORDS:
        await open_conversion_menu(update, context)
        return

    if normalized in DATE_KEYWORDS:
        await prompt_for_date(update, context)
        return

    await update.message.reply_text(
        "Не понял запрос. Используйте кнопки меню или введите число для конвертации."
    )


async def _handle_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        selected_date = datetime.strptime(text, "%d.%m.%Y")
    except ValueError:
        await update.message.reply_text(
            "Неверный формат даты. Используйте ДД.ММ.ГГГГ или нажмите '🏠 Меню'."
        )
        return

    context.user_data['selected_date'] = selected_date
    context.user_data['awaiting_date'] = False
    await show_main_menu(update, context, info_message="Дата обновлена.")


async def _handle_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.replace(',', '.').strip()
    try:
        amount = float(text)
    except ValueError:
        await update.message.reply_text(
            "Введите только число или используйте кнопки меню для других действий."
        )
        return

    base_currency = context.user_data.get('base_currency')
    target_currency = context.user_data.get('target_currency')
    rates = context.user_data.get('rates')

    if not base_currency or not target_currency or not rates:
        await update.message.reply_text(
            "Не удалось определить валюты. Нажмите '💱 Конвертация' и выберите пару заново."
        )
        return

    result = convert_amount(amount, base_currency, target_currency, rates)
    if result is None:
        await update.message.reply_text(
            "Курс для выбранной пары сейчас недоступен. Попробуйте другую дату или валюту."
        )
        return

    context.user_data['awaiting_amount'] = False

    response_date = context.user_data.get('response_date')
    date_label = response_date or context.user_data['selected_date'].strftime('%d.%m.%Y')

    message = (
        f"{_format_amount(amount)} {base_currency} = {_format_amount(result)} {target_currency}\n"
        f"Курсы ЦБ РФ на {date_label}"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔁 Новая конвертация", callback_data="convert_menu")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
        ]
    )

    await update.message.reply_text(message, reply_markup=keyboard)


def convert_amount(amount: float, base: str, target: str, rates: dict) -> Optional[float]:
    """Пересчёт суммы через рубль как базовую единицу."""

    if base not in ALL_CURRENCIES or target not in ALL_CURRENCIES:
        return None

    base_rate = rates.get(base, 1.0 if base == "RUB" else None)
    target_rate = rates.get(target, 1.0 if target == "RUB" else None)

    if base_rate in (None, 0) or target_rate in (None, 0):
        return None

    amount_in_rub = amount if base == "RUB" else amount * base_rate
    if target == "RUB":
        return amount_in_rub
    return amount_in_rub / target_rate


def _format_amount(value: float) -> str:
    return f"{value:,.2f}".replace(",", " ")


async def prompt_for_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запросить дату у пользователя."""
    context.user_data['awaiting_date'] = True
    context.user_data['awaiting_amount'] = False

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]]
    )

    text = "Введите дату в формате ДД.ММ.ГГГГ."

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)


async def change_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await prompt_for_date(update, context)


async def go_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update, context)

def main():
    """Основной цикл бота."""
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(go_to_main_menu, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(open_conversion_menu, pattern="^convert_menu$"))
    application.add_handler(CallbackQueryHandler(select_base_currency, pattern="^base:"))
    application.add_handler(CallbackQueryHandler(select_target_currency, pattern="^target:"))
    application.add_handler(CallbackQueryHandler(change_date, pattern="^change_date$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    application.run_polling()

if __name__ == "__main__":
    main()
