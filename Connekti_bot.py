import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from flask import Flask, request
import logging
import threading
import time

# -------------------- Config --------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BOT_TOKEN = os.getenv("BOT_TOKEN")
PAYPAL_EMAIL = os.getenv("PAYPAL_EMAIL")  # your PayPal email
BASE_URL = os.getenv("BASE_URL")  # your server URL for PayPal IPN (https://yourdomain.com/ipn)

if not BOT_TOKEN or not PAYPAL_EMAIL or not BASE_URL:
    raise ValueError("Please set BOT_TOKEN, PAYPAL_EMAIL, and BASE_URL environment variables.")

bot = telebot.TeleBot(BOT_TOKEN)

# -------------------- Flask App for PayPal --------------------
app = Flask(__name__)

# Store pending orders {payment_id: {"chat_id": x, "file": y}}
pending_orders = {}

@app.route("/ipn", methods=["POST"])
def paypal_ipn():
    data = request.form.to_dict()
    logging.info(f"Received IPN: {data}")

    # Minimal validation
    if data.get("payment_status") == "Completed" and data.get("receiver_email") == PAYPAL_EMAIL:
        custom_id = data.get("custom")  # we pass this in PayPal link
        if custom_id in pending_orders:
            order = pending_orders.pop(custom_id)
            chat_id = order["chat_id"]
            file_path = order["file"]

            bot.send_message(chat_id, "✅ Payment received! Here’s your lead file:")
            with open(file_path, "rb") as f:
                bot.send_document(chat_id, InputFile(f, os.path.basename(file_path)))
    return "OK", 200

# -------------------- Bot Handlers --------------------
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📂 Standard Leads ($10)", callback_data="standard"))
    markup.add(InlineKeyboardButton("📂 Premium Leads ($20)", callback_data="premium"))

    bot.send_message(
        message.chat.id,
        "👋 Welcome to *Connekti Lead Shop*!\n\nChoose a lead package below:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data in ["standard", "premium"])
def handle_package(call):
    package = call.data
    price = 10 if package == "standard" else 20
    file_path = f"sample_{package}.csv"

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔎 Sample Leads", callback_data=f"sample_{package}"))
    markup.add(InlineKeyboardButton("💳 Buy Now", url=generate_paypal_link(call.from_user.id, package, price)))

    bot.send_message(
        call.message.chat.id,
        f"You selected *{package.title()} Leads* (${price}).\n\nChoose an option below:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("sample_"))
def send_sample(call):
    package = call.data.replace("sample_", "")
    file_path = f"sample_{package}.csv"
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            bot.send_document(call.message.chat.id, InputFile(f, os.path.basename(file_path)))
    else:
        bot.send_message(call.message.chat.id, "❌ Sample file not found.")

# -------------------- Helper --------------------
def generate_paypal_link(user_id, package, price):
    """Generate PayPal payment link with IPN support"""
    payment_id = f"{user_id}_{int(time.time())}"
    pending_orders[payment_id] = {
        "chat_id": user_id,
        "file": f"{package}_leads.csv"
    }

    return (
        f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick"
        f"&business={PAYPAL_EMAIL}"
        f"&item_name={package.title()} Leads"
        f"&amount={price}"
        f"&currency_code=USD"
        f"&notify_url={BASE_URL}/ipn"
        f"&custom={payment_id}"
    )

# -------------------- Run Bot + Server --------------------
def run_bot():
    while True:
        try:
            logging.info("Connekti_bot starting...")
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            logging.error(f"Bot crashed: {e}. Restarting in 5s...")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=5000)
