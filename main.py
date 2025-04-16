from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
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

# Админ ID
ADMIN_ID = 1611776955

# Память
user_data = {}
greeted_users = set()

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

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data[user_id]["branch"] = query.data

    await query.message.reply_text("Спасибо за информацию, давайте сверим все введенные Вами данные для исключения возможных опечаток.")

    await query.message.reply_text(summary_text(user_id))

    keyboard = [
        [InlineKeyboardButton("Да, все верно!", callback_data="confirm")],
        [InlineKeyboardButton("Нет, есть ошибка", callback_data="error")],
    ]
    await query.message.reply_text("Все верно?", reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRMATION

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

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "confirm":
        d = user_data[user_id]
        msg = (
            f"Имя родителя: {d.get('parent_name')}\n"
            f"Телефон родителя: {d.get('phone')}\n"
            f"Филиал: {d.get('branch')}\n"
            f"Имя и фамилия ребенка: {d.get('child_name')}\n"
            f"Возраст ребенка: {d.get('child_age')}\n"
            f"Класс ребенка: {d.get('child_class')}\n"
            f"Смена ребенка: {d.get('shift')}\n"
            f"Познания в области Английского языка: {d.get('english_level')}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
        await query.message.reply_text("Спасибо! Ваша информация успешно отправлена администратору.")
        return ConversationHandler.END
    else:
        keyboard = [
            [InlineKeyboardButton("Имя Родителя", callback_data="parent_name")],
            [InlineKeyboardButton("Телефон", callback_data="phone")],
            [InlineKeyboardButton("Филиал", callback_data="branch")],
            [InlineKeyboardButton("Имя ребенка", callback_data="child_name")],
            [InlineKeyboardButton("Возраст ребенка", callback_data="child_age")],
            [InlineKeyboardButton("Класс ребенка", callback_data="child_class")],
            [InlineKeyboardButton("Смена ребенка", callback_data="shift")],
        ]
        await query.message.reply_text("Пожалуйста укажите где была совершена ошибка", reply_markup=InlineKeyboardMarkup(keyboard))
        return CORRECTION_SELECT

async def handle_correction_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["correction_field"] = query.data

    questions = {
        "parent_name": "Как к Вам можно обращаться?",
        "phone": "Укажите свой номер телефона, по которому мы вышлем подходящее расписание.",
        "branch": "Выберите филиал ещё раз:",
        "child_name": "Укажите имя и фамилию ребенка.",
        "child_age": "Укажите возраст ребенка",
        "child_class": "Скажите, пожалуйста, в каком классе Ваш ребенок?",
        "shift": "В какую смену учится ребенок?",
    }

    if query.data == "branch":
        keyboard = [
            [InlineKeyboardButton("Ул Авроры 17/2", callback_data="Ул Авроры 17/2")],
            [InlineKeyboardButton("Ул Революционая,78", callback_data="Ул Революционая,78")],
            [InlineKeyboardButton("Ул Баландина 2а", callback_data="Ул Баландина 2а")],
            [InlineKeyboardButton("Онлайн-школа", callback_data="Онлайн-школа")],
        ]
        await query.message.reply_text(
            questions[query.data], reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ASK_BRANCH

    await query.message.reply_text(questions[query.data])
    return CORRECTION_INPUT

async def handle_correction_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    field = context.user_data["correction_field"]
    user_data[user_id][field] = update.message.text

    await update.message.reply_text("Хорошо, я исправил выбранные Вами данные!")
    await update.message.reply_text(summary_text(user_id))

    keyboard = [
        [InlineKeyboardButton("Да, все верно!", callback_data="confirm")],
        [InlineKeyboardButton("Нет, есть ошибка", callback_data="error")],
    ]
    await update.message.reply_text("Все верно?", reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRMATION

# Главный запуск
if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()
    app = ApplicationBuilder().token(os.getenv("7910071726:AAFgHCgGpGA2j1mNZdL5N8xm9jhd4VC2gMU")).build()

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

    app.add_handler(conv_handler)
    app.run_polling()
