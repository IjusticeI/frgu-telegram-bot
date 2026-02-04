# bot.py
import os
import logging
from flask import Flask, request, jsonify
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from google.cloud import dialogflow_v2 as dialogflow
from google.api_core.client_options import ClientOptions
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Flask-сервер для Render ===
app = Flask(__name__)

# === Настройки ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DIALOGFLOW_PROJECT_ID = os.getenv("DIALOGFLOW_PROJECT_ID")
DIALOGFLOW_LANGUAGE_CODE = "ru"

# Проверка переменных окружения
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не задан в переменных окружения!")
if not DIALOGFLOW_PROJECT_ID:
    raise ValueError("DIALOGFLOW_PROJECT_ID не задан в переменных окружения!")

# Глобальная переменная для приложения Telegram
telegram_app = None

# Функция для инициализации Telegram-бота (асинхронная)
async def init_telegram_app():
    global telegram_app
    telegram_app = await Application.builder().token(TELEGRAM_TOKEN).build()
    logger.info("Telegram-бот инициализирован")

# Функция для Dialogflow
def detect_intent_text(text, user_id):
    session_client = dialogflow.SessionsClient(
        client_options=ClientOptions(api_endpoint="dialogflow.googleapis.com")
    )
    session = session_client.session_path(DIALOGFLOW_PROJECT_ID, f"sessions/{user_id}")

    text_input = dialogflow.TextInput(text=text, language_code=DIALOGFLOW_LANGUAGE_CODE)
    query_input = dialogflow.QueryInput(text=text_input)

    try:
        response = session_client.detect_intent(request={"session": session, "query_input": query_input})
        return response.query_result.fulfillment_text
    except Exception as e:
        logger.error(f"Ошибка Dialogflow: {e}")
        return "Сейчас не могу ответить. Попробуйте позже."

# === Обработчики ===
async def start(update, context):
    await update.message.reply_text("Здравствуйте! Я ваш бот-помощник в работе с ФРГУ!")

async def handle_message(update, context):
    user_message = update.message.text
    user_id = update.effective_user.id
    ai_response = detect_intent_text(user_message, user_id)
    await update.message.reply_text(ai_response)

# === Вебхук для Telegram (с фиксированным URL) ===
@app.route("/webhook", methods=["POST"])
def webhook():
    request_data = request.get_json()
    from telegram import Update  # Явный импорт
    update = Update.de_json(request_data, telegram_app.bot)
    
    # Асинхронное выполнение process_update
    asyncio.run(telegram_app.process_update(update))
    return "ok", 200

@app.route("/")
def home():
    return "<h1>Бот работает!</h1>", 200

# Функция для настройки обработчиков
def setup_handlers():
    global telegram_app
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Обработчики зарегистрированы")

# Запуск приложения
async def main():
    # Инициализация Telegram-бота
    await init_telegram_app()
    # Настройка обработчиков
    setup_handlers()
    # Запуск Flask-сервера
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

if __name__ == "__main__":
    # Запуск асинхронного основного метода
    asyncio.run(main())
