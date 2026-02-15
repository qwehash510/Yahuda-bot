import json
import logging
import os
import time
from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")

STAFF_FILE = "staff.json"
PROTECT_FILE = "protect.json"
SPAM = {}

logging.basicConfig(level=logging.INFO)

# JSON oluştur
def load_json(file, default):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return default

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

staff = load_json(STAFF_FILE, {
    "kurucu": [],
    "yardimci": [],
    "admin": [],
    "mod": [],
    "susturucu": []
})

protect = load_json(PROTECT_FILE, {
    "link": True,
    "spam": True
})

# USERNAME al
def get_username(user):
    return f"@{user.username}" if user.username else user.first_name

# YETKİ KONTROL
def is_staff(username):
    for role in staff:
        if username in staff[role]:
            return True
    return False

def is_kurucu(username):
    return username in staff["kurucu"]

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_username(update.effective_user)

    if not staff["kurucu"]:
        staff["kurucu"].append(user)
        save_json(STAFF_FILE, staff)
        await update.message.reply_text(
            f"👑 {user} artık Kurucu!\n\nYAHUDA #KABİLE AKTİF"
        )
    else:
        await update.message.reply_text("YAHUDA #KABİLE aktif.")

# STAFF LİSTE
async def staff_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = "⚡ YAHUDA #KABİLE STAFF\n\n"

    roles = {
        "kurucu": "👑 Kurucu",
        "yardimci": "⚜ Yardımcı Kurucu",
        "admin": "🛡 Admin",
        "mod": "🔧 Moderatör",
        "susturucu": "🔇 Susturucu"
    }

    for key, name in roles.items():
        text += f"{name}\n"
        if staff[key]:
            for u in staff[key]:
                text += f"• {u}\n"
        else:
            text += "• yok\n"
        text += "\n"

    await update.message.reply_text(text)

# YETKİ VER
async def give_role(update: Update, context: ContextTypes.DEFAULT_TYPE, role):

    sender = get_username(update.effective_user)

    if not is_kurucu(sender):
        return await update.message.reply_text("Yetkin yok.")

    if not update.message.reply_to_message:
        return await update.message.reply_text("Bir mesaja reply yap.")

    target = get_username(update.message.reply_to_message.from_user)

    if target not in staff[role]:
        staff[role].append(target)
        save_json(STAFF_FILE, staff)

    await update.message.reply_text(f"{target} artık {role}")

async def kurucu(update, context):
    await give_role(update, context, "kurucu")

async def yardimci(update, context):
    await give_role(update, context, "yardimci")

async def admin(update, context):
    await give_role(update, context, "admin")

async def mod(update, context):
    await give_role(update, context, "mod")

async def susturucu(update, context):
    await give_role(update, context, "susturucu")

# YETKİ AL
async def yetkial(update: Update, context: ContextTypes.DEFAULT_TYPE):

    sender = get_username(update.effective_user)

    if not is_kurucu(sender):
        return

    target = get_username(update.message.reply_to_message.from_user)

    for role in staff:
        if target in staff[role]:
            staff[role].remove(target)

    save_json(STAFF_FILE, staff)

    await update.message.reply_text("Yetki alındı.")

# BAN
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):

    sender = get_username(update.effective_user)

    if not is_staff(sender):
        return

    user = update.message.reply_to_message.from_user

    await update.effective_chat.ban_member(user.id)

    await update.message.reply_text("Banlandı.")

# KICK
async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):

    sender = get_username(update.effective_user)

    if not is_staff(sender):
        return

    user = update.message.reply_to_message.from_user

    await update.effective_chat.ban_member(user.id)
    await update.effective_chat.unban_member(user.id)

    await update.message.reply_text("Atıldı.")

# MUTE
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):

    sender = get_username(update.effective_user)

    if not is_staff(sender):
        return

    user = update.message.reply_to_message.from_user

    await update.effective_chat.restrict_member(
        user.id,
        ChatPermissions(can_send_messages=False)
    )

    await update.message.reply_text("Susturuldu.")

# UNMUTE
async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):

    sender = get_username(update.effective_user)

    if not is_staff(sender):
        return

    user = update.message.reply_to_message.from_user

    await update.effective_chat.restrict_member(
        user.id,
        ChatPermissions(can_send_messages=True)
    )

    await update.message.reply_text("Susturma kaldırıldı.")

# HOŞGELDİN
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):

    for user in update.message.new_chat_members:

        username = get_username(user)

        await update.message.reply_text(
            f"⚡ YAHUDA #KABİLE\n\nHoşgeldin {username}"
        )

# HOŞÇAKAL
async def bye(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.left_chat_member

    username = get_username(user)

    await update.message.reply_text(
        f"{username} ayrıldı."
    )

# LINK KORUMA
async def protect_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if protect["link"]:

        text = update.message.text.lower()

        if "http" in text or "t.me" in text:

            user = get_username(update.effective_user)

            if not is_staff(user):

                await update.message.delete()

# PING
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚡ Aktif")

# MAIN
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("staff", staff_cmd))

app.add_handler(CommandHandler("kurucu", kurucu))
app.add_handler(CommandHandler("yardimci", yardimci))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("mod", mod))
app.add_handler(CommandHandler("susturucu", susturucu))

app.add_handler(CommandHandler("yetkial", yetkial))

app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("kick", kick))
app.add_handler(CommandHandler("mute", mute))
app.add_handler(CommandHandler("unmute", unmute))

app.add_handler(CommandHandler("ping", ping))

app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, bye))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, protect_msg))

print("YAHUDA #KABİLE EFSANE v3 AKTİF")

app.run_polling()
