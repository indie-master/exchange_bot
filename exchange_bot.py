import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, Updater, CallbackContext

# Вставьте ваш API ключ
API_KEY = '52073917cd526850614660da'

# Эндпоинты для разных валют
BASE_URL_USD = f'https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD'
BASE_URL_EUR = f'https://v6.exchangerate-api.com/v6/{API_KEY}/latest/EUR'
BASE_URL_CNY = f'https://v6.exchangerate-api.com/v6/{API_KEY}/latest/CNY'


async def fetch_exchange_rates():
    """Получить курсы валют."""
    response_usd = requests.get(BASE_URL_USD).json()
    response_eur = requests.get(BASE_URL_EUR).json()
    response_cny = requests.get(BASE_URL_CNY).json()

    return {
        'USD': response_usd['conversion_rates'].get('RUB', "Не доступно"),
        'EUR': response_eur['conversion_rates'].get('RUB', "Не доступно"),
        'CNY': response_cny['conversion_rates'].get('RUB', "Не доступно")
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
    )

    keyboard = [
        [InlineKeyboardButton("Посмотреть курсы валют", callback_data="view_rates")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(message, reply_markup=reply_markup)


async def view_rates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать кнопки выбора валют."""
    keyboard = [
        [InlineKeyboardButton("USD к RUB", callback_data="USD")],
        [InlineKeyboardButton("EUR к RUB", callback_data="EUR")],
        [InlineKeyboardButton("CNY к RUB", callback_data="CNY")],
        [InlineKeyboardButton("Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("Выберите валюту:", reply_markup=reply_markup)


async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню ввода суммы для расчёта."""
    query = update.callback_query
    currency = query.data

    context.user_data['selected_currency'] = currency
    rate = context.user_data['rates'].get(currency, "Не доступно")

    if rate == "Не доступно":
        await query.edit_message_text(f"Курс для {currency} недоступен.")
        return

    keyboard = [[InlineKeyboardButton("Назад", callback_data="view_rates")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=f"Введите сумму в {currency}, чтобы конвертировать в RUB:",
        reply_markup=reply_markup
    )


async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработать ввод суммы пользователем."""
    try:
        amount = float(update.message.text)
        currency = context.user_data.get('selected_currency')
        rate = context.user_data['rates'].get(currency)

        if not currency or not rate:
            await update.message.reply_text("Произошла ошибка. Пожалуйста, начните с команды /start.")
            return

        result = amount * rate

        # Клавиатура после расчета
        keyboard = [
            [InlineKeyboardButton("Выбрать другую валюту", callback_data="view_rates")],
            [InlineKeyboardButton("Назад в главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text=f"{amount} {currency} = {result:.2f} RUB\n\nЧто хотите сделать дальше?",
            reply_markup=reply_markup
        )
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число.")


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в главное меню."""
    await start(update, context)


async def back_to_rates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возвращает пользователя в меню выбора валют."""
    keyboard = [
        [InlineKeyboardButton("USD к RUB", callback_data="USD"), 
         InlineKeyboardButton("EUR к RUB", callback_data="EUR"),
         InlineKeyboardButton("CNY к RUB", callback_data="CNY")],
        [InlineKeyboardButton("Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.edit_text(
        text="Выберите валюту для конвертации:",
        reply_markup=reply_markup
    )


def main():
    """Основной цикл бота."""
    application = Application.builder().token("7957019843:AAF1LnZTCNZt6RLhr3HLxeL7VQpbUh00dlo").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(view_rates, pattern="view_rates"))
    application.add_handler(CallbackQueryHandler(calculate, pattern="^(USD|EUR|CNY)$"))
    application.add_handler(CallbackQueryHandler(back_to_main, pattern="back_to_main"))
    application.add_handler(CallbackQueryHandler(back_to_rates, pattern="view_rates"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount))

    application.run_polling()


if __name__ == "__main__":
    main()
