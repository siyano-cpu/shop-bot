import os
import sqlite3
import telebot

from flask import Flask, request
from database import init_db

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")  # مهم: مستقیم از Render

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not found")

init_db()

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ------------------------
# DATABASE
# ------------------------

def db():
    return sqlite3.connect("shop.db")

# ------------------------
# WEBHOOK SET (درست و امن)
# ------------------------

@app.before_first_request
def setup_webhook():
    try:
        bot.remove_webhook()
        bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
        print("✅ Webhook set:", WEBHOOK_URL)
    except Exception as e:
        print("❌ Webhook error:", e)

# ------------------------
# START
# ------------------------

@bot.message_handler(commands=["start"])
def start(message):
    conn = db()
    conn.execute(
        "INSERT OR IGNORE INTO users(telegram_id, username) VALUES(?,?)",
        (message.from_user.id, message.from_user.username)
    )
    conn.commit()
    conn.close()

    bot.reply_to(message, "به فروشگاه خوش آمدید ✅\n\n/products")

# ------------------------
# PRODUCTS
# ------------------------

@bot.message_handler(commands=["products"])
def products(message):
    conn = db()
    rows = conn.execute("SELECT id,title,price FROM products").fetchall()
    conn.close()

    if not rows:
        bot.reply_to(message, "محصولی وجود ندارد")
        return

    text = "📦 محصولات:\n\n"
    for r in rows:
        text += f"ID:{r[0]}\n{r[1]}\n💰{r[2]}\n/order_{r[0]}\n\n"

    bot.reply_to(message, text)

# ------------------------
# ORDER
# ------------------------

@bot.message_handler(func=lambda m: m.text and m.text.startswith("/order_"))
def order(message):
    product_id = int(message.text.split("_")[1])

    conn = db()
    user = conn.execute(
        "SELECT id FROM users WHERE telegram_id=?",
        (message.from_user.id,)
    ).fetchone()

    conn.execute(
        "INSERT INTO orders(user_id, product_id) VALUES(?,?)",
        (user[0], product_id)
    )

    order_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    conn.commit()
    conn.close()

    bot.reply_to(message, f"✅ سفارش ثبت شد #{order_id}")

# ------------------------
# FLASK ROUTES
# ------------------------

@app.route("/")
def home():
    return "Shop Bot Running"

@app.route("/webhook", methods=["POST"])
def webhook():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

# ------------------------
# RUN
# ------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
