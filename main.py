import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, ContextTypes,
    ConversationHandler, MessageHandler, CallbackQueryHandler,
    filters
)
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Пример: https://your-bot.onrender.com

# Состояния
(
    ASK_PARENT_NAME, ASK_CHILD_NAME, ASK_CHILD_AGE, ASK_CHILD_CLASS,
    ASK_SHIFT, ASK_ENGLISH_LEVEL, ASK_PHONE, ASK_BRANCH,
    CONFIRMATION, CORRECTION_SELECT, CORRECTION_INPUT
) = range(11)

ADMIN_ID = 1611776955
user_data = {}
greeted_users = set()

# --- Хендлеры команд и логики ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {}

    if user_id not in greeted_users:
        greeted_users.add(user_id)
        await update.message.reply_text(
            "Здравствуйте! С Вами на связи бот-помощник Языкового центра Smart+ ..."
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
    await update.message.reply_text("В каком классе ваш ребёнок?")
    return ASK_CHILD_CLASS

async def ask_shift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["child_class"] = update.message.text
    await update.message.reply_text("В какую смену учится ребёнок?")
    return ASK_SHIFT

async def ask_english_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["shift"] = update.message.text
    await update.message.reply_text("Как дела с английским?")
    return ASK_ENGLISH_LEVEL

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["english_level"] = update.message.text
    await update.message.reply_text("Укажите номер телефона.")
    return ASK_PHONE

async def ask_branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["phone"] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Ул Авроры 17/2", callback_data="Ул Авроры 17/2")],
        [InlineKeyboardButton("Ул Революционая,78", callback_data="Ул Революционая,78")],
        [InlineKeyboardButton("Ул Баландина 2а", callback_data="Ул Баландина 2а")],
        [InlineKeyboardButton("Онлайн-школа", callback_data="Онлайн-школа")],
    ]
    await update.message.reply_text("Выберите филиал:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ASK_BRANCH

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data[user_id]["branch"] = query.data

    await query.message.reply_text("Сверим данные:")
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
        await query.message.reply_text("Спасибо! Мы свяжемся с Вами.")
        return ConversationHandler.END
    else:
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
        await query.message.reply_text("Что нужно исправить?", reply_markup=InlineKeyboardMarkup(keyboard))
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
    await update.message.reply_text("Обновлено. Вот новая версия:")
    await update.message.reply_text(summary_text(user_id))
    keyboard = [
        [InlineKeyboardButton("Да, все верно!", callback_data="confirm")],
        [InlineKeyboardButton("Нет, есть ошибка", callback_data="error")]
    ]
    await update.message.reply_text("Все верно?", reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRMATION

def summary_text(user_id):
    d = user_data[user_id]
    return (
        f"Имя родителя: {d.get('parent_name')}\n"
        f"Телефон родителя: {d.get('phone')}\n"
        f"Филиал: {d.get('branch')}\n"
        f"Имя ребенка: {d.get('child_name')}\n"
        f"Возраст: {d.get('child_age')}\n"
        f"Класс: {d.get('child_class')}\n"
        f"Смена: {d.get('shift')}\n"
        f"Английский: {d.get('english_level')}"
    )

# --- Запуск приложения ---

if __name__ == "__main__":
    application = Application.builder().token(TOKEN).build()

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

    # Установка вебхука
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )
