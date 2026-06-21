import os
import telebot
from flask import Flask, request

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not found")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)


# ---------------- HOME ----------------
@app.route("/")
def home():
    return "Bot is running ✅"


# ---------------- WEBHOOK ----------------
@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_str = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "OK", 200
    return "Bad Request", 400


# ---------------- COMMANDS ----------------
@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "ربات فعال است ✅")


@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.reply_to(message, "/start - شروع\n/help - راهنما")


# ---------------- START WEBHOOK (IMPORTANT) ----------------
def setup_webhook():
    try:
        bot.remove_webhook()
        bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
        print("Webhook set successfully")
    except Exception as e:
        print("Webhook error:", e)


# ---------------- MAIN ----------------
if __name__ == "__main__":
    setup_webhook()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
