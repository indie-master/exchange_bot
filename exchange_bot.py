import requests
import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение токенов
BOT_TOKEN = os.getenv('BOT_TOKEN')
API_KEY = os.getenv('API_KEY')

if not BOT_TOKEN or not API_KEY:
    raise ValueError("Не удалось загрузить BOT_TOKEN или API_KEY. Проверьте файл .env.")

# Эндпоинты для разных валют
BASE_URL_RUB = f'https://v6.exchangerate-api.com/v6/{API_KEY}/latest/RUB'
BASE_URL_USD = f'https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD'
BASE_URL_EUR = f'https://v6.exchangerate-api.com/v6/{API_KEY}/latest/EUR'
BASE_URL_CNY = f'https://v6.exchangerate-api.com/v6/{API_KEY}/latest/CNY'

async def fetch_exchange_rates():
    """Получить курсы валют."""
    try:
        response_rub = requests.get(BASE_URL_RUB).json()
        response_usd = requests.get(BASE_URL_USD).json()
        response_eur = requests.get(BASE_URL_EUR).json()
        response_cny = requests.get(BASE_URL_CNY).json()

        return {
            'USD': response_usd['conversion_rates'].get('RUB', None),
            'EUR': response_eur['conversion_rates'].get('RUB', None),
            'CNY': response_cny['conversion_rates'].get('RUB', None),
            'RUB': response_rub['conversion_rates'].get('USD', None)
        }
    except Exception as e:
        print(f"Ошибка при получении курсов валют: {e}")
        return {
            'USD': None,
            'EUR': None,
            'CNY': None,
            'RUB': None
        }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню бота."""
    rates = await fetch_exchange_rates()
    context.user_data['rates'] = rates

    message = (
        f"Курс валют на текущий момент:\n"
        f"1 USD = {rates['USD']} RUB\n"
        f"1 EUR = {rates['EUR']} RUB\n"
        f"1 CNY = {rates['CNY']} RUB\n"
        f"1 RUB = {rates['RUB']} USD\n"
    )

    keyboard = [
        [InlineKeyboardButton("Конвертировать из RUB", callback_data="convert_from_rub")],
        [InlineKeyboardButton("Конвертировать в RUB", callback_data="convert_to_rub")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:  # Если update.message существует
        await update.message.reply_text(message, reply_markup=reply_markup)
    elif update.callback_query:  # Если update.callback_query существует
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup)

async def convert_from_rub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор валюты для конвертации из рубля."""
    keyboard = [
        [InlineKeyboardButton("USD", callback_data="RUB_to_USD")],
        [InlineKeyboardButton("EUR", callback_data="RUB_to_EUR")],
        [InlineKeyboardButton("CNY", callback_data="RUB_to_CNY")],
        [InlineKeyboardButton("Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Выберите валюту для конвертации из RUB:", reply_markup=reply_markup)

async def convert_to_rub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор валюты для конвертации в рубли."""
    keyboard = [
        [InlineKeyboardButton("USD", callback_data="USD_to_RUB")],
        [InlineKeyboardButton("EUR", callback_data="EUR_to_RUB")],
        [InlineKeyboardButton("CNY", callback_data="CNY_to_RUB")],
        [InlineKeyboardButton("Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Выберите валюту для конвертации в RUB:", reply_markup=reply_markup)

async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню ввода суммы для расчёта."""
    query = update.callback_query
    currency = query.data

    context.user_data['selected_currency'] = currency
    rates = context.user_data['rates']

    if 'to_RUB' in currency:
        currency = currency.split('_')[0]  # Получаем валюту (USD, EUR, CNY)

    rate = rates.get(currency)

    if rate is None:
        await query.edit_message_text(f"Курс для {currency} недоступен.")
        return

    keyboard = [[InlineKeyboardButton("Назад", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=f"Введите сумму в {currency}, чтобы конвертировать:",
        reply_markup=reply_markup
    )

async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработать ввод суммы пользователем."""
    try:
        amount = float(update.message.text)
        currency = context.user_data.get('selected_currency')
        rates = context.user_data['rates']

        if not currency or not rates:
            await update.message.reply_text("Произошла ошибка. Пожалуйста, начните с команды /start.")
            return

        if 'to_RUB' in currency:
            # Конвертация в рубли
            rate = rates[currency.split('_')[0]]  # Получаем соответствующую валюту
            if rate is None:
                await update.message.reply_text(f"Курс для {currency} недоступен.")
                return
            result = amount * rate
            message = f"{amount} {currency.split('_')[0]} = {result:.2f} RUB"
        else:
            # Конвертация из рубля
            rate = rates.get(currency)
            if rate is None:
                await update.message.reply_text(f"Курс для {currency} недоступен.")
                return
            result = amount / rate
            message = f"{amount} RUB = {result:.2f} {currency}"

        # Клавиатура после расчета
        keyboard = [
            [InlineKeyboardButton("Выбрать другую валюту", callback_data="view_rates")],
            [InlineKeyboardButton("Назад в главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.message:
            await update.message.reply_text(
                text=message,
                reply_markup=reply_markup
            )
        elif update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                text=message,
                reply_markup=reply_markup
            )
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число.")

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в главное меню."""
    query = update.callback_query
    await start(update, context)

def main():
    """Основной цикл бота."""
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(convert_from_rub, pattern="convert_from_rub"))
    application.add_handler(CallbackQueryHandler(convert_to_rub, pattern="convert_to_rub"))
    application.add_handler(CallbackQueryHandler(calculate, pattern="^(USD_to_RUB|EUR_to_RUB|CNY_to_RUB|RUB_to_USD|RUB_to_EUR|RUB_to_CNY)$"))
    application.add_handler(CallbackQueryHandler(back_to_main, pattern="back_to_main"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount))

    application.run_polling()

if __name__ == "__main__":
    main()
