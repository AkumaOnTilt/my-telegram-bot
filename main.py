from flask import Flask, request
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, ContextTypes,
    ConversationHandler, MessageHandler, CallbackQueryHandler,
    filters
)
import os

# Состояния
(
    ASK_PARENT_NAME, ASK_CHILD_NAME, ASK_CHILD_AGE, ASK_CHILD_CLASS,
    ASK_SHIFT, ASK_ENGLISH_LEVEL, ASK_PHONE, ASK_BRANCH,
    CONFIRMATION, CORRECTION_SELECT, CORRECTION_INPUT
) = range(11)

ADMIN_ID = 1611776955
user_data = {}
greeted_users = set()

app = Flask(__name__)

# --- ОБРАБОТЧИКИ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {}

    if user_id not in greeted_users:
        greeted_users.add(user_id)
        await update.message.reply_text(
            "Здравствуйте! С Вами на связи бот-помощник Языкового центра Smart+\n"
            "Smart+ это:\n"
            "- Оксфордская программа, лицензия министерства образования;\n"
            "- Рождественской фестиваль, Театральный фестиваль на сцене университета для всех родителей;\n"
            "- Государственный сертификат о получении уровня владения языком, торжественное вручение на сцене университета;\n"
            "- Встречи с иностранцами в разговорных клубах каждый месяц;\n"
            "- Свой выездной полилингвальный приключенческий лагерь Гринхил на всех каникулах"
        )

    await update.message.reply_text("Как к Вам можно обращаться?")
    return ASK_PARENT_NAME

async def ask_child_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["parent_name"] = update.message.text
    await update.message.reply_text("Укажите имя и фамилию ребенка.")
    return ASK_CHILD_NAME

async def ask_child_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["child_name"] = update.message.text
    await update.message.reply_text("Укажите возраст ребенка")
    return ASK_CHILD_AGE

async def ask_child_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["child_age"] = update.message.text
    await update.message.reply_text("Скажите, пожалуйста, в каком классе Ваш ребенок?")
    return ASK_CHILD_CLASS

async def ask_shift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["child_class"] = update.message.text
    await update.message.reply_text("В какую смену учится ребенок?")
    return ASK_SHIFT

async def ask_english_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["shift"] = update.message.text
    await update.message.reply_text("Как обстоят дела с английским языком? Изучали ли до этого дополнительно? Какая оценка в школе?")
    return ASK_ENGLISH_LEVEL

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["english_level"] = update.message.text
    await update.message.reply_text("Укажите свой номер телефона, по которому мы вышлем подходящее расписание.")
    return ASK_PHONE

async def ask_branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["phone"] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Ул Авроры 17/2", callback_data="Ул Авроры 17/2")],
        [InlineKeyboardButton("Ул Революционая,78", callback_data="Ул Революционая,78")],
        [InlineKeyboardButton("Ул Баландина 2а", callback_data="Ул Баландина 2а")],
        [InlineKeyboardButton("Онлайн-школа", callback_data="Онлайн-школа")],
    ]
    await update.message.reply_text(
        "В каком филиале Вам удобнее заниматься?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ASK_BRANCH

# --- ОБРАБОТКА ВЫБОРА ФИЛИАЛА ---

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data[user_id]["branch"] = query.data

    await query.message.reply_text("Спасибо за информацию, давайте сверим все введенные Вами данные для исключения возможных опечаток.")
    await query.message.reply_text(summary_text(user_id))

    keyboard = [
        [InlineKeyboardButton("Да, все верно!", callback_data="confirm")],
        [InlineKeyboardButton("Нет, есть ошибка", callback_data="error")]
    ]
    await query.message.reply_text("Все верно?", reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRMATION

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if query.data == "confirm":
        await context.bot.send_message(ADMIN_ID, f"Новая заявка:\n{summary_text(user_id)}")
        await query.message.reply_text("Спасибо! Мы свяжемся с Вами в ближайшее время.")
        return ConversationHandler.END
    elif query.data == "error":
        keyboard = [
            [InlineKeyboardButton("Имя родителя", callback_data="parent_name")],
            [InlineKeyboardButton("Имя ребенка", callback_data="child_name")],
            [InlineKeyboardButton("Возраст", callback_data="child_age")],
            [InlineKeyboardButton("Класс", callback_data="child_class")],
            [InlineKeyboardButton("Смена", callback_data="shift")],
            [InlineKeyboardButton("Английский", callback_data="english_level")],
            [InlineKeyboardButton("Телефон", callback_data="phone")],
            [InlineKeyboardButton("Филиал", callback_data="branch")],
        ]
        await query.message.reply_text("Что Вы хотите изменить?", reply_markup=InlineKeyboardMarkup(keyboard))
        return CORRECTION_SELECT

async def handle_correction_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["field_to_correct"] = query.data
    await query.message.reply_text("Введите новое значение:")
    return CORRECTION_INPUT

async def handle_correction_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    field = context.user_data.get("field_to_correct")
    if field:
        user_data[user_id][field] = update.message.text
    await update.message.reply_text("Исправлено. Вот обновленная информация:")
    await update.message.reply_text(summary_text(user_id))
    keyboard = [
        [InlineKeyboardButton("Да, все верно!", callback_data="confirm")],
        [InlineKeyboardButton("Нет, есть ошибка", callback_data="error")]
    ]
    await update.message.reply_text("Все верно?", reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRMATION

# --- СУММАРНЫЙ ТЕКСТ ---
def summary_text(user_id):
    d = user_data[user_id]
    return (
        f"Имя родителя: {d.get('parent_name')}\n"
        f"Телефон родителя: {d.get('phone')}\n"
        f"Филиал: {d.get('branch')}\n"
        f"Имя и фамилия ребенка: {d.get('child_name')}\n"
        f"Возраст ребенка: {d.get('child_age')}\n"
        f"Класс ребенка: {d.get('child_class')}\n"
        f"Смена ребенка: {d.get('shift')}\n"
        f"Английский: {d.get('english_level')}"
    )

# --- WEBHOOK ROUTE ---
@app.route(f"/{os.getenv('BOT_TOKEN')}", methods=["POST"])
def webhook():
    json_str = request.get_data(as_text=True)
    update = Update.de_json(json_str, app.bot)
    app.bot.loop.create_task(app.process_update(update))
    return 'OK', 200

# --- MAIN ---
if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()

    TOKEN = os.getenv("BOT_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")

    application = Application.builder().token(TOKEN).build()
    app.bot = application.bot
    app.process_update = application.process_update

    # Conversation
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_PARENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_child_name)],
            ASK_CHILD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_child_age)],
            ASK_CHILD_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_child_class)],
            ASK_CHILD_CLASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_shift)],
            ASK_SHIFT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_english_level)],
            ASK_ENGLISH_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_branch)],
            ASK_BRANCH: [CallbackQueryHandler(confirm)],
            CONFIRMATION: [CallbackQueryHandler(handle_confirmation)],
            CORRECTION_SELECT: [CallbackQueryHandler(handle_correction_choice)],
            CORRECTION_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_correction_input)],
        },
        fallbacks=[]
    )

    application.add_handler(conv_handler)

    # Установка webhook
    async def run():
        WEBHOOK_BASE = "https://my-telegram-bot.onrender.com"
        BOT_TOKEN = os.getenv("BOT_TOKEN")

        await application.bot.set_webhook(f"{WEBHOOK_BASE}/{BOT_TOKEN}")
        print("Webhook установлен")

    import asyncio
    asyncio.run(run())

    # Запуск Flask
    app.run(host="0.0.0.0", port=5000)
