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
def send_buy(message):
    leads = LEAD_FILES.split(",")
    reply = "📂 Available Leads:\n"
    for idx, lead in enumerate(leads, start=1):
        reply += f"{idx}. {lead.strip()}\n"
    reply += f"\n💳 Pay via PayPal: {PAYPAL_EMAIL}\nOnce paid, your file will be sent automatically."
    bot.reply_to(message, reply)

# --- Webhook route for Telegram ---
@server.route(f"/{BOT_TOKEN}", methods=['POST'])
def telegram_webhook():
    json_str = request.stream.read().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# --- Health check (optional) ---
@server.route("/", methods=['GET'])
def index():
    return "🤖 Connekti Bot is running!", 200

if __name__ == "__main__":
    # Important: tell Telegram where to send updates
    if BASE_URL:
        webhook_url = f"{BASE_URL}/{BOT_TOKEN}"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)

    port = int(os.environ.get("PORT", 10000))
    server.run(host="0.0.0.0", port=port)
