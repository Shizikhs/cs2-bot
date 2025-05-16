import os
import logging
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, CallbackQueryHandler, ContextTypes
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Шаги формы
CHOOSING_STREAMER, GET_TWITCH, GET_SCREENSHOT, GET_ITEM, GET_TRADELINK, CONFIRM = range(6)

ADMIN_ID = 868478841
TRADE_BAN_DAYS = 8

user_data_store = {}
completed_requests = []

def format_date():
    return datetime.now().strftime("%d.%m.%Y")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Rusi4TV", callback_data="Rusi4TV"),
         InlineKeyboardButton("A_S_L", callback_data="A_S_L")]
    ]
    await update.message.reply_text("Привет! От какого стримера ты пришел?", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSING_STREAMER

async def streamer_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["streamer"] = query.data
    context.user_data["username"] = query.from_user.username or query.from_user.full_name
    await query.message.reply_text("Напиши свой Twitch ник:")
    return GET_TWITCH

async def get_twitch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["twitch_nick"] = update.message.text
    await update.message.reply_text("Отправь скриншот своего Twitch аккаунта:")
    return GET_SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["screenshot"] = update.message.photo[-1].file_id
    await update.message.reply_text("Какой предмет ты выиграл?")
    return GET_ITEM

async def get_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["item"] = update.message.text
    context.user_data["date"] = format_date()
    await update.message.reply_text("Вставь свою трейд-ссылку:")
    return GET_TRADELINK

async def get_tradelink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["tradelink"] = update.message.text

    username = context.user_data["username"]
    if username not in user_data_store:
        user_data_store[username] = []

    user_data_store[username].append(context.user_data.copy())

    # Уведомление админу
    msg = f"Новая заявка:\nПользователь: @{username}\nСтример: {context.user_data['streamer']}\nTwitch: {context.user_data['twitch_nick']}\nПредмет: {context.user_data['item']}\nДата: {context.user_data['date']}\nТрейд: {context.user_data['tradelink']}"
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=context.user_data["screenshot"], caption=msg, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("Заявка выполнена", callback_data=f"done|{username}|{context.user_data['date']}")]
    ]))

    # Сообщение пользователю
    await update.message.reply_text("Заявка отправлена!")
    await update.message.reply_text("Присоединяйся в наш [дискорд](https://discord.gg/3AQ4nHZxtk) 🎉", parse_mode="Markdown")
    await update.message.reply_text("Хочешь узнать, сколько осталось до конца трейд-бана?",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Проверить", callback_data=f"ban|{context.user_data['date']}")]])
    )
    return ConversationHandler.END

async def trade_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, date_str = query.data.split("|")
    claim_date = datetime.strptime(date_str, "%d.%m.%Y")

    days_passed = (datetime.now() - claim_date).days
    remaining = TRADE_BAN_DAYS - days_passed

    await query.answer()
    if remaining > 0:
        await query.edit_message_text(f"До окончания трейд-бана осталось {remaining} дней")
    else:
        await query.edit_message_text("Трейд-бан истек, вы можете получить предмет.")

async def mark_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, username, date = query.data.split("|")
    completed_requests.append((username, date))
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"Заявка от @{username} от {date} отмечена как выполненная.")
    await context.bot.send_message(chat_id=query.from_user.id, text="Ваша заявка выполняется, пожалуйста, примите трейд")
    await query.answer("Заявка отмечена как выполненная.")
    await query.edit_message_reply_markup(None)

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Нет доступа.")
        return

    keyboard = [
        [InlineKeyboardButton("Все заявки", callback_data="show_all")],
        [InlineKeyboardButton("Выполненные", callback_data="show_done")]
    ]
    await update.message.reply_text("Админ-панель", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "show_all":
        msg = "Все заявки:\n"
        for user, entries in user_data_store.items():
            for e in entries:
                msg += f"@{user} | {e['item']} | {e['date']}\n"
        await query.edit_message_text(msg or "Нет заявок.")
    elif query.data == "show_done":
        msg = "Выполненные заявки:\n"
        for u, d in completed_requests:
            msg += f"@{u} | {d}\n"
        await query.edit_message_text(msg or "Нет выполненных заявок.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_STREAMER: [CallbackQueryHandler(streamer_choice)],
            GET_TWITCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_twitch)],
            GET_SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot)],
            GET_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_item)],
            GET_TRADELINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tradelink)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(trade_status, pattern="^ban\|"))
    app.add_handler(CallbackQueryHandler(mark_done, pattern="^done\|"))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(show_requests, pattern="^show_"))

    app.run_polling()

if __name__ == "__main__":
    main()