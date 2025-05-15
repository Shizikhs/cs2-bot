
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, CallbackQueryHandler, filters, ConversationHandler
)
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 868478841

(
    CHOOSE_SENDER,
    ENTER_TWITCH_NICK,
    UPLOAD_SCREENSHOT,
    ENTER_ITEM,
    ENTER_STREAM_DATE,
    ENTER_TRADE_LINK,
    FINISHED
) = range(7)

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Rusi4TV", callback_data='Rusi4TV')],
        [InlineKeyboardButton("A_S_L", callback_data='A_S_L')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите отправителя:", reply_markup=reply_markup)
    return CHOOSE_SENDER

async def choose_sender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data[query.from_user.id] = {'sender': query.data}
    await query.edit_message_text(f"Вы выбрали: {query.data}\nВведите ваш ник на Twitch:")
    return ENTER_TWITCH_NICK

async def enter_twitch_nick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]['twitch_nick'] = update.message.text
    await update.message.reply_text("Загрузите скриншот Twitch аккаунта:")
    return UPLOAD_SCREENSHOT

async def upload_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Пожалуйста, отправьте изображение.")
        return UPLOAD_SCREENSHOT
    photo_file_id = update.message.photo[-1].file_id
    user_data[update.effective_user.id]['screenshot'] = photo_file_id
    await update.message.reply_text("Введите предмет:")
    return ENTER_ITEM

async def enter_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]['item'] = update.message.text
    await update.message.reply_text("Введите дату стрима:")
    return ENTER_STREAM_DATE

async def enter_stream_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]['stream_date'] = update.message.text
    await update.message.reply_text("Введите трейд-ссылку:")
    return ENTER_TRADE_LINK

async def enter_trade_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]['trade_link'] = update.message.text
    data = user_data[update.effective_user.id]
    text = (
        f"📥 Новая заявка:\n\n"
        f"👤 Отправитель: {data['sender']}\n"
        f"🎮 Twitch ник: {data['twitch_nick']}\n"
        f"🎁 Предмет: {data['item']}\n"
        f"📅 Дата стрима: {data['stream_date']}\n"
        f"🔗 Трейд-ссылка: {data['trade_link']}"
    )
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=data['screenshot'], caption=text)
    await update.message.reply_text("✅ Ваша заявка отправлена!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Заявка отменена.")
    return ConversationHandler.END

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Доступ запрещён.")
        return
    await update.message.reply_text("👑 Добро пожаловать в админ-панель!\n(Пока что доступна только проверка заявок через Telegram)")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_SENDER: [CallbackQueryHandler(choose_sender)],
            ENTER_TWITCH_NICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_twitch_nick)],
            UPLOAD_SCREENSHOT: [MessageHandler(filters.PHOTO, upload_screenshot)],
            ENTER_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_item)],
            ENTER_STREAM_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_stream_date)],
            ENTER_TRADE_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_trade_link)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("admin", admin))

    app.run_polling()

if __name__ == "__main__":
    main()
