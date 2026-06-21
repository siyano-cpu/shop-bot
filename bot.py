import os
import sqlite3
import telebot

from flask import Flask, request
from database import init_db

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

ADMIN_ID = 123456789

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not found")

if not WEBHOOK_URL:
    raise Exception("WEBHOOK_URL not found")

init_db()

bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

# ------------------------
# WEBHOOK
# ------------------------

bot.remove_webhook()
bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

# ------------------------
# DATABASE
# ------------------------

def db():
    return sqlite3.connect("shop.db")

# ------------------------
# START
# ------------------------

@bot.message_handler(commands=["start"])
def start(message):

    conn = db()

    conn.execute(
        """
        INSERT OR IGNORE INTO users(
            telegram_id,
            username
        )
        VALUES(?,?)
        """,
        (
            message.from_user.id,
            message.from_user.username
        )
    )

    conn.commit()
    conn.close()

    bot.reply_to(
        message,
        "به فروشگاه خوش آمدید ✅\n\n/products"
    )

# ------------------------
# PRODUCTS
# ------------------------

@bot.message_handler(commands=["products"])
def products(message):

    conn = db()

    products = conn.execute(
        """
        SELECT id,title,price
        FROM products
        """
    ).fetchall()

    conn.close()

    if not products:
        bot.reply_to(message, "محصولی وجود ندارد")
        return

    text = "📦 محصولات:\n\n"

    for p in products:
        text += f"""
ID: {p[0]}
{p[1]}
💰 {p[2]} تومان

/order_{p[0]}

"""

    bot.reply_to(message, text)

# ------------------------
# ORDER
# ------------------------

@bot.message_handler(func=lambda m: m.text.startswith("/order_"))
def order(message):

    product_id = int(
        message.text.replace("/order_", "")
    )

    conn = db()

    user = conn.execute(
        """
        SELECT id
        FROM users
        WHERE telegram_id=?
        """,
        (message.from_user.id,)
    ).fetchone()

    conn.execute(
        """
        INSERT INTO orders(
            user_id,
            product_id
        )
        VALUES(?,?)
        """,
        (
            user[0],
            product_id
        )
    )

    order_id = conn.execute(
        "SELECT last_insert_rowid()"
    ).fetchone()[0]

    conn.commit()
    conn.close()

    bot.reply_to(
        message,
        f"✅ سفارش #{order_id} ثبت شد"
    )

    bot.send_message(
        ADMIN_ID,
        f"""
📦 سفارش جدید

شماره:
{order_id}

کاربر:
{message.from_user.id}

محصول:
{product_id}
"""
    )

# ------------------------
# ADMIN APPROVE
# ------------------------

@bot.message_handler(commands=["orders"])
def orders(message):

    if message.from_user.id != ADMIN_ID:
        return

    conn = db()

    rows = conn.execute(
        """
        SELECT id,status
        FROM orders
        ORDER BY id DESC
        LIMIT 20
        """
    ).fetchall()

    conn.close()

    text = ""

    for row in rows:
        text += f"""
#{row[0]}
{row[1]}

"""

    bot.send_message(message.chat.id, text)

# ------------------------
# HOME
# ------------------------

@app.route("/")
def home():
    return "Shop Bot Running"

# ------------------------
# WEBHOOK
# ------------------------

@app.route("/webhook", methods=["POST"])
def webhook():

    if request.headers.get(
        "content-type"
    ) == "application/json":

        json_string = request.get_data().decode(
            "utf-8"
        )

        update = telebot.types.Update.de_json(
            json_string
        )

        bot.process_new_updates([update])

        return "OK", 200

    return "Bad Request", 400

# ------------------------
# MAIN
# ------------------------

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 5000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )