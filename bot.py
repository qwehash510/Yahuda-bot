import json
import logging
import os
from datetime import datetime, timedelta

from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# TOKEN Railway'den alınır
TOKEN = os.getenv("BOT_TOKEN")

# Logging
logging.basicConfig(level=logging.INFO)

DATA_FILE = "data.json"

# Varsayılan veri
DEFAULT_DATA = {
    "founders": [],
    "co_founders": [],
    "admins": [],
    "muted": {},
    "banned": [],
    "protection": False
}

# Veri yükle
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA

# Veri kaydet
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()


# Yetki kontrol
def is_founder(user_id):
    return user_id in data["founders"]

def is_co_founder(user_id):
    return user_id in data["co_founders"]

def is_admin(user_id):
    return user_id in data["admins"]

def is_staff(user_id):
    return (
        is_founder(user_id)
        or is_co_founder(user_id)
        or is_admin(user_id)
    )


# İlk kurucu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not data["founders"]:
        data["founders"].append(user_id)
        save_data(data)
        await update.message.reply_text(
            "☠️ YAHUDA #KABİLE\n"
            "Kurucu olarak atandın."
        )
        return

    await update.message.reply_text(
        "☠️ YAHUDA #KABİLE aktif."
    )


# Staff list
async def staff(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = "☠️ YAHUDA STAFF\n\n"

    text += "Kurucular:\n"
    for i in data["founders"]:
        text += f"- {i}\n"

    text += "\nYardımcı Kurucular:\n"
    for i in data["co_founders"]:
        text += f"- {i}\n"

    text += "\nAdminler:\n"
    for i in data["admins"]:
        text += f"- {i}\n"

    await update.message.reply_text(text)


# Admin ver
async def adminver(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.reply_to_message

    if not user:
        return

    uid = user.from_user.id

    if not is_founder(update.effective_user.id):
        return

    if uid not in data["admins"]:
        data["admins"].append(uid)
        save_data(data)

    await update.message.reply_text("Admin verildi.")


# Admin al
async def adminal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.reply_to_message

    if not user:
        return

    uid = user.from_user.id

    if not is_founder(update.effective_user.id):
        return

    if uid in data["admins"]:
        data["admins"].remove(uid)
        save_data(data)

    await update.message.reply_text("Admin alındı.")


# Ban
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_staff(update.effective_user.id):
        return

    msg = update.message.reply_to_message

    if not msg:
        return

    uid = msg.from_user.id

    await context.bot.ban_chat_member(
        update.effective_chat.id,
        uid
    )

    await update.message.reply_text("Kullanıcı banlandı.")


# Kick
async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_staff(update.effective_user.id):
        return

    msg = update.message.reply_to_message

    if not msg:
        return

    uid = msg.from_user.id

    await context.bot.ban_chat_member(
        update.effective_chat.id,
        uid
    )

    await context.bot.unban_chat_member(
        update.effective_chat.id,
        uid
    )

    await update.message.reply_text("Kullanıcı atıldı.")


# Mute
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_staff(update.effective_user.id):
        return

    msg = update.message.reply_to_message

    if not msg:
        return

    uid = msg.from_user.id

    permissions = ChatPermissions(
        can_send_messages=False
    )

    await context.bot.restrict_chat_member(
        update.effective_chat.id,
        uid,
        permissions
    )

    await update.message.reply_text("Susturuldu.")


# Unmute
async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_staff(update.effective_user.id):
        return

    msg = update.message.reply_to_message

    if not msg:
        return

    uid = msg.from_user.id

    permissions = ChatPermissions(
        can_send_messages=True
    )

    await context.bot.restrict_chat_member(
        update.effective_chat.id,
        uid,
        permissions
    )

    await update.message.reply_text("Susturma kaldırıldı.")


# Koruma aç
async def korumaac(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_founder(update.effective_user.id):
        return

    data["protection"] = True
    save_data(data)

    await update.message.reply_text("Koruma açıldı.")


# Koruma kapat
async def korumakapat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_founder(update.effective_user.id):
        return

    data["protection"] = False
    save_data(data)

    await update.message.reply_text("Koruma kapatıldı.")


# Hoşgeldin
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):

    for user in update.message.new_chat_members:

        await update.message.reply_text(
            f"☠️ YAHUDA #KABİLE\n"
            f"Hoşgeldin {user.first_name}"
        )


# Hoşçakal
async def goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.left_chat_member

    await update.message.reply_text(
        f"{user.first_name} ayrıldı."
    )


# Main
def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("staff", staff))
    app.add_handler(CommandHandler("adminver", adminver))
    app.add_handler(CommandHandler("adminal", adminal))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("korumaac", korumaac))
    app.add_handler(CommandHandler("korumakapat", korumakapat))

    app.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome)
    )

    app.add_handler(
        MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, goodbye)
    )

    print("YAHUDA #KABİLE AKTİF")

    app.run_polling()


if __name__ == "__main__":
    main()
