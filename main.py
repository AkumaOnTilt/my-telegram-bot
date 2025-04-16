import os
from flask import Flask, request
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    ConversationHandler, MessageHandler, CallbackQueryHandler,
    filters
)
import dotenv

# Загружаем переменные окружения
dotenv.load_dotenv()

# Состояния
(
    ASK_PARENT_NAME, ASK_CHILD_NAME, ASK_CHILD_AGE, ASK_CHILD_CLASS,
    ASK_SHIFT, ASK_ENGLISH_LEVEL, ASK_PHONE, ASK_BRANCH,
    CONFIRMATION, CORRECTION_SELECT, CORRECTION_INPUT
) = range(11)

# Админ ID
ADMIN_ID = 1611776955

# Память
user_data = {}
greeted_users = set()

# Flask приложение
app = Flask(__name__)

# Старт
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

# Все другие асинхронные функции, такие как ask_child_name, ask_child_age и т.д. остаются без изменений
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

# Вспомогательная функция для создания summary
def summary_text(user_id):
    d = user_data[user_id]
    return (
        f"Имя родителя: {d.get('parent_name')}\n"
        f"Телефон родителя: {d.get('phone')}\n"
        f"Филиал: {d.get('branch')}\n"
        f"Имя и фамилия ребенка: {d.get('child_name')}\n"
        f"Возраст ребенка: {d.get('child_age')}\n"
        f"Класс ребенка: {d.get('child_class')}\n"
        f"Смена ребенка: {d.get('shift')}"
    )

# Конфигурация webhook
async def set_webhook(application: ApplicationBuilder):
    webhook_url = f"https://my-telegram-bot.onrender.com/{os.getenv('BOT_TOKEN')}"
    await application.bot.set_webhook(webhook_url)
    print("Webhook установлен")

# Обработчик для подтверждения и исправлений
async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Тут должна быть логика для обработки подтверждения
    pass

# Определим функцию confirm, которая использовалась в CallbackQueryHandler
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Вы подтвердили ваш выбор!")

# Обработчики для разных частей формы
# (оставляем без изменений)

# Webhook endpoint для Flask
@app.route(f"/{os.getenv('BOT_TOKEN')}", methods=["POST"])
def webhook():
    json_str = request.get_data(as_text=True)
    update = Update.de_json(json_str, app.bot)
    app.process_update(update)
    return 'OK', 200

# Главный запуск
async def main():
    # Инициализация приложения
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    # Устанавливаем webhook
    await set_webhook(app)  # Добавляем await

    # Конфигурация ConversationHandler
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
            ASK_BRANCH: [CallbackQueryHandler(confirm)],  # Убедитесь, что confirm теперь определен
            CONFIRMATION: [CallbackQueryHandler(handle_confirmation)],
            CORRECTION_SELECT: [CallbackQueryHandler(handle_correction_choice)],
            CORRECTION_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_correction_input)],
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.run(host="0.0.0.0", port=5000)  # Flask сервер для получения webhook

# Вызов функции main
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())  # Запуск асинхронной функции main
