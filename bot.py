
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)
from datetime import datetime, timedelta

FROM, NICK, SCREENSHOT, ITEM, TRADELINK, STREAM_DATE, BAN_DAYS = range(7)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет, Антон!\nОт кого заявка? (Rusi4TV / A_S_L)")
    return FROM

async def from_sender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["from"] = update.message.text.strip()
    await update.message.reply_text("Укажи свой ник на Twitch:")
    return NICK

async def twitch_nick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nick"] = update.message.text.strip()
    await update.message.reply_text("Пришли скриншот аккаунта на Twitch:")
    return SCREENSHOT

async def twitch_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data["screenshot_file_id"] = update.message.photo[-1].file_id
        await update.message.reply_text("Какой предмет (скин) ты выиграл?")
        return ITEM
    else:
        await update.message.reply_text("Пожалуйста, пришли **фото**, а не текст.")
        return SCREENSHOT

async def item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["item"] = update.message.text.strip()
    await update.message.reply_text("Вставь свою трейд-ссылку:")
    return TRADELINK

async def trade_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["tradelink"] = update.message.text.strip()
    await update.message.reply_text("Укажи дату стрима (например: 12.05.2025):")
    return STREAM_DATE

async def stream_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["date"] = update.message.text.strip()
    await update.message.reply_text("Через сколько дней спадёт трейд-бан?")
    return BAN_DAYS

async def ban_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        days = int(update.message.text.strip())
        unban_date = datetime.now() + timedelta(days=days)
        context.user_data["ban_days"] = days
        context.user_data["unban_date"] = unban_date.strftime("%d.%m.%Y")

        data = context.user_data
        message = (
            f"📩 Заявка на скин:\n\n"
            f"👤 Привет, Антон!\n"
            f"👥 От: {data['from']}\n"
            f"🎮 Twitch ник: {data['nick']}\n"
            f"🎁 Предмет: {data['item']}\n"
            f"🔗 Трейд-ссылка: {data['tradelink']}\n"
            f"📅 Дата стрима: {data['date']}\n"
            f"⏳ Трейд-бан спадёт: {data['unban_date']} (через {data['ban_days']} дней)"
        )

        await update.message.reply_photo(
            photo=data["screenshot_file_id"],
            caption=message
        )
        await update.message.reply_text("✅ Заявка отправлена. Спасибо!")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Введите число, например: 8")
        return BAN_DAYS

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Заявка отменена.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token("7689057554:AAGLXbPd6s_S8aMJfLgnw1Bhie53i3IZ5NE").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, from_sender)],
            NICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, twitch_nick)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, twitch_screenshot)],
            ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, item)],
            TRADELINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, trade_link)],
            STREAM_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, stream_date)],
            BAN_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ban_days)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
