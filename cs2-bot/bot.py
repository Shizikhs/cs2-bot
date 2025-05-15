from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
)
import datetime

# Этапы диалога
FROM, TWITCH_NAME, SCREENSHOT, ITEM, TRADE_LINK, STREAM_DATE, TRADEBAN_DAYS = range(7)

# Старт команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет, Антон!\nВыбери, от кого заявка:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton("Rusi4TV")], [KeyboardButton("A_S_L")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    return FROM

# Выбор отправителя
async def from_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["from"] = update.message.text
    await update.message.reply_text("Напиши свой ник на Twitch:")
    return TWITCH_NAME

async def twitch_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["twitch_name"] = update.message.text
    await update.message.reply_text("Отправь скриншот аккаунта на Twitch:")
    return SCREENSHOT

async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data["screenshot"] = update.message.photo[-1].file_id
    else:
        await update.message.reply_text("Пожалуйста, отправь именно СКРИНШОТ.")
        return SCREENSHOT

    await update.message.reply_text("Укажи название предмета:")
    return ITEM

async def item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["item"] = update.message.text
    await update.message.reply_text("Вставь трейд-ссылку:")
    return TRADE_LINK

async def trade_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["trade_link"] = update.message.text
    await update.message.reply_text("Укажи дату стрима (в формате ГГГГ-ММ-ДД):")
    return STREAM_DATE

async def stream_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["stream_date"] = update.message.text
    await update.message.reply_text("Через сколько дней спадёт трейд-бан?")
    return TRADEBAN_DAYS

async def tradeban_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        days = int(update.message.text)
        date_unban = datetime.date.today() + datetime.timedelta(days=days)
        context.user_data["unban_date"] = date_unban.strftime("%Y-%m-%d")
    except ValueError:
        await update.message.reply_text("Введите число — количество дней до снятия трейд-бана.")
        return TRADEBAN_DAYS

    data = context.user_data
    await update.message.reply_photo(
        photo=data["screenshot"],
        caption=(
            f"📬 Заявка:\n"
            f"👤 От: {data['from']}\n"
            f"🎮 Twitch: {data['twitch_name']}\n"
            f"🎁 Предмет: {data['item']}\n"
            f"🔗 Трейд-ссылка: {data['trade_link']}\n"
            f"📅 Дата стрима: {data['stream_date']}\n"
            f"⏳ Трейд-блок до: {data['unban_date']}"
        )
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Окей, отменено.")
    return ConversationHandler.END

# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token("7689057554:AAGLXbPd6s_S8aMJfLgnw1Bhie53i3IZ5NE").build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, from_handler)],
            TWITCH_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, twitch_name)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, screenshot)],
            ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, item)],
            TRADE_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, trade_link)],
            STREAM_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, stream_date)],
            TRADEBAN_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, tradeban_days)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    print("✅ Бот запущен.")
    app.run_polling()
