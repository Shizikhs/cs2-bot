
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters, ConversationHandler
)
import os

SENDER, TWITCH_NICK, TWITCH_SCREENSHOT, ITEM, TRADE_LINK, STREAM_DATE = range(6)

applications = []

ADMIN_IDS = [123456789]  # Замените на свой Telegram ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Rusi4TV", callback_data="Rusi4TV"),
         InlineKeyboardButton("A_S_L", callback_data="A_S_L")]
    ]
    await update.message.reply_text("Выберите отправителя:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SENDER

async def sender_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["sender"] = query.data
    await query.message.reply_text("Введите ваш ник на Twitch:")
    return TWITCH_NICK

async def twitch_nick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["twitch_nick"] = update.message.text
    await update.message.reply_text("Пришлите скриншот аккаунта на Twitch:")
    return TWITCH_SCREENSHOT

async def twitch_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Пожалуйста, пришлите изображение.")
        return TWITCH_SCREENSHOT
    photo_file = update.message.photo[-1].file_id
    context.user_data["screenshot"] = photo_file
    await update.message.reply_text("Укажите предмет:")
    return ITEM

async def item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["item"] = update.message.text
    await update.message.reply_text("Вставьте трейд-ссылку:")
    return TRADE_LINK

async def trade_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["trade_link"] = update.message.text
    await update.message.reply_text("Укажите дату стрима:")
    return STREAM_DATE

async def stream_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["stream_date"] = update.message.text

    applications.append(context.user_data.copy())

    await update.message.reply_text("Спасибо, ваша заявка принята!")
    return ConversationHandler.END

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("У вас нет доступа.")
        return
    if not applications:
        await update.message.reply_text("Нет новых заявок.")
        return
    text = ""
    for i, app in enumerate(applications, 1):
        text += (f"Заявка #{i}\n"
                 f"Отправитель: {app['sender']}\n"
                 f"Twitch: {app['twitch_nick']}\n"
                 f"Предмет: {app['item']}\n"
                 f"Ссылка: {app['trade_link']}\n"
                 f"Дата: {app['stream_date']}\n\n")
    await update.message.reply_text(text)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(os.getenv("7689057554:AAGLXbPd6s_S8aMJfLgnw1Bhie53i3IZ5NE")).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SENDER: [CallbackQueryHandler(sender_chosen)],
            TWITCH_NICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, twitch_nick)],
            TWITCH_SCREENSHOT: [MessageHandler(filters.PHOTO, twitch_screenshot)],
            ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, item)],
            TRADE_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, trade_link)],
            STREAM_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, stream_date)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("admin", admin))

    app.run_polling()

if __name__ == "__main__":
    main()
