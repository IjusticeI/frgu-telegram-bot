# bot.py
import os
from flask import Flask, request, jsonify
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from google.cloud import dialogflow_v2 as dialogflow
from google.api_core.client_options import ClientOptions

# === Flask-сервер для Render ===
app = Flask(__name__)

# === Настройки ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DIALOGFLOW_PROJECT_ID = os.getenv("DIALOGFLOW_PROJECT_ID")
DIALOGFLOW_LANGUAGE_CODE = "ru"

# Инициализация Telegram-бота
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

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
        print(f"Ошибка Dialogflow: {e}")
        return "Сейчас не могу ответить. Попробуйте позже."

# === Обработчики ===
async def start(update, context):
    await update.message.reply_text("Здравствуйте Я ваш бот-помощник в работе с ФРГУ!")

async def handle_message(update, context):
    user_message = update.message.text
    user_id = update.effective_user.id
    ai_response = detect_intent_text(user_message, user_id)
    await update.message.reply_text(ai_response)

# === Вебхук для Telegram ===
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    request_data = request.get_json()
    update = telegram.update.Update.de_json(request_data, telegram_app.bot)
    telegram_app.process_update(update)
    return "ok", 200

@app.route("/")
def home():
    return "<h1>Бот работает!</h1>", 200

# Запуск приложения (для локального теста)
if __name__ == "__main__":
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))