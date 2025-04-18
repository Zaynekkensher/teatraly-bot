import json
import logging
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, WebAppInfo, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from flask import Flask, request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TOKEN')  # теперь лучше хранить в переменных окружения
EVENTS_FILE = 'events.json'

app = Flask(__name__)

# загрузка данных событий
def load_events():
    try:
        with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# сохранение данных событий
def save_events(events):
    with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton(text="➕ Добавить мероприятие", web_app=WebAppInfo(url="https://zaynekkensher.github.io/-teatraly-webapp/"))],
        [KeyboardButton(text="📋 Список мероприятий")],
        [KeyboardButton(text="✏️ Редактировать"), KeyboardButton(text="🔄 Перенести")],
        [KeyboardButton(text="🗑 Удалить мероприятие")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Добро пожаловать в 'Театралы' 🎭!", reply_markup=reply_markup)

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    data = json.loads(update.message.web_app_data.data)

    try:
        datetime.strptime(data["date"], "%d.%m.%Y")
        datetime.strptime(data["time"], "%H:%M")
    except ValueError:
        await update.message.reply_text("⚠️ Неверный формат даты или времени. Используйте календарь и часы.")
        return

    events = load_events()
    if chat_id not in events:
        events[chat_id] = []
    events[chat_id].append(data)
    save_events(events)

    await update.message.reply_text("✅ Мероприятие добавлено!")

async def list_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    events = load_events().get(chat_id, [])
    if not events:
        await update.message.reply_text("Список мероприятий пуст 🗓️")
        return
    events.sort(key=lambda e: datetime.strptime(e['date'] + ' ' + e['time'], '%d.%m.%Y %H:%M'))
    msg = "📅 Все мероприятия:\n\n"
    for e in events:
        event_date = datetime.strptime(e['date'] + ' ' + e['time'], '%d.%m.%Y %H:%M')
        now = datetime.now()
        if event_date < now:
            msg += f"🔘 {e['date']} {e['time']} (прошло)\n"
        else:
            msg += f"🟢 {e['date']} {e['time']}\n"
        msg += f"🏷 {e['title']} | {e['place']}\n📍 {e['city']}\n📝 {e['comment']}\n\n"
    await update.message.reply_text(msg)

# веб-хук для Telegram
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook_handler():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok", 200

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list", list_events))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^📋 Список мероприятий$"), list_events))

    # webhook-режим, порт для Render
    port = int(os.environ.get("PORT", 5000))
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TOKEN,
        webhook_url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"
    )