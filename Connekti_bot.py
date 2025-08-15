import os
import telebot
from flask import Flask, request

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
PAYPAL_EMAIL = os.getenv("PAYPAL_EMAIL")
LEAD_FILES = os.getenv("LEAD_FILES", "")  # Comma-separated filenames
BASE_URL = os.getenv("BASE_URL")  # e.g. https://connekti-bot.onrender.com

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)

# --- Bot commands ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "🤖 Welcome to the Lead Shop Bot!\nUse /buy to see available leads.")

@bot.message_handler(commands=['buy'])
def send_files(message):
    if not LEAD_FILES:
        bot.reply_to(message, "No files are available right now.")
        return
    
    files = LEAD_FILES.split(",")
    response = "📂 Available leads:\n"
    for f in files:
        response += f" - {f.strip()}\n"
    response += f"\nTo buy, send payment to PayPal: {PAYPAL_EMAIL}"
    bot.send_message(message.chat.id, response)

# --- Flask routes ---
@server.route(f"/{BOT_TOKEN}", methods=["POST"])
def get_message():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/", methods=["GET"])
def index():
    return "🤖 Connekti Bot is running!", 200

# --- Setup webhook ---
if __name__ == "__main__":
    # Remove previous webhook (safety)
    bot.remove_webhook()

    # Set webhook to your Render BASE_URL
    webhook_url = f"{BASE_URL}/{BOT_TOKEN}"
    bot.set_webhook(url=webhook_url)

    # Start Flask server (Render runs gunicorn normally)
   
