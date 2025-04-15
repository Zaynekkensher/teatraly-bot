import json
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EVENTS_FILE = 'events.json'

def load_events():
    try:
        with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_events(events):
    with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        {
            "text": "Добавить мероприятие",
            "web_app": WebAppInfo(url="https://zaynekkensher.github.io/-teatraly-webapp/")
        }
    ]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Добро пожаловать в 'Театралы' 🎭!", reply_markup=reply_markup)

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.message.web_app_data.data)
        events = load_events()
        events.append(data)
        save_events(events)
        await update.message.reply_text("✅ Мероприятие добавлено!")
    except Exception as e:
        logger.error(f"Ошибка при обработке данных из формы: {e}")
        await update.message.reply_text("⚠️ Ошибка при добавлении мероприятия")

async def list_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    events = load_events()
    if not events:
        await update.message.reply_text("Список мероприятий пуст 🗓️")
        return
    msg = "📅 Все мероприятия:\n\n"
    for e in events:
        msg += f"{e['date']} {e['time']} — {e['title']}\n📍 {e['place']}\n📝 {e['comment']}\n\n"
    await update.message.reply_text(msg)

async def next_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    events = load_events()
    if not events:
        await update.message.reply_text("Нет запланированных мероприятий")
        return
    events.sort(key=lambda e: datetime.strptime(e['date'] + ' ' + e['time'], '%d.%m.%Y %H:%M'))
    next_e = events[0]
    msg = (f"🎯 Ближайшее мероприятие:\n\n{next_e['date']} {next_e['time']} — {next_e['title']}\n"
           f"📍 {next_e['place']}\n📝 {next_e['comment']}")
    await update.message.reply_text(msg)

if __name__ == '__main__':
    app = ApplicationBuilder().token("8054569637:AAERIvbdTeyicVAibj79w7A4yDmd5JKxfeA").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_events))
    app.add_handler(CommandHandler("next", next_event))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    print("Бот запущен...")
    app.run_polling()