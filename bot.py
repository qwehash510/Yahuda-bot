import json
import logging
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =====================
# AYARLAR
# =====================

BOT_TOKEN = "BOT_TOKEN_BURAYA"
OWNER_ID = 8464933639  # KENDİ TELEGRAM ID

DATA_FILE = "data.json"

logging.basicConfig(level=logging.INFO)

# =====================
# DATA
# =====================

def load():
    try:
        with open(DATA_FILE) as f:
            return json.load(f)
    except:
        return {
            "founder": None,
            "cofounders": [],
            "admins": [],
            "mods": [],
            "muted": []
        }

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load()

# =====================
# YARDIMCI
# =====================

def is_founder(username):
    return username == data["founder"]

def is_cofounder(username):
    return username in data["cofounders"]

def is_admin(username):
    return username in data["admins"]

def is_mod(username):
    return username in data["mods"]

def is_staff(username):
    return (
        username == data["founder"]
        or username in data["cofounders"]
        or username in data["admins"]
        or username in data["mods"]
    )

# =====================
# START (SADECE SEN)
# =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Bu bot özel.")
        return

    username = update.effective_user.username

    if not data["founder"]:
        data["founder"] = username
        save(data)

    await update.message.reply_text(
        "YAHUDA #KRALLIK BOT AKTİF\n"
        "Kurucu olarak tanımlandın.\n\n"
        "/panel yaz"
    )

# =====================
# PANEL
# =====================

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    username = update.effective_user.username

    if not is_staff(username):
        return

    await update.message.reply_text(
        "YAHUDA #KRALLIK PANEL\n\n"
        "/staff\n"
        "/ban @user\n"
        "/unban @user\n"
        "/mute @user\n"
        "/unmute @user\n"
        "/kick @user\n"
        "/addadmin @user\n"
        "/addmod @user\n"
        "/addco @user"
    )

# =====================
# STAFF PANEL
# =====================

async def staff(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = "YAHUDA #KRALLIK STAFF\n\n"

    if data["founder"]:
        text += f"Kurucu: @{data['founder']}\n\n"

    if data["cofounders"]:
        text += "Yardımcı Kurucu:\n"
        for u in data["cofounders"]:
            text += f" @{u}\n"
        text += "\n"

    if data["admins"]:
        text += "Admin:\n"
        for u in data["admins"]:
            text += f" @{u}\n"
        text += "\n"

    if data["mods"]:
        text += "Mod:\n"
        for u in data["mods"]:
            text += f" @{u}\n"

    await update.message.reply_text(text)

# =====================
# YETKİ VERME
# =====================

async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.username != data["founder"]:
        return

    user = context.args[0].replace("@", "")

    if user not in data["admins"]:
        data["admins"].append(user)
        save(data)

    await update.message.reply_text("Admin eklendi")

async def addmod(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.username not in data["admins"]:
        return

    user = context.args[0].replace("@", "")

    if user not in data["mods"]:
        data["mods"].append(user)
        save(data)

    await update.message.reply_text("Mod eklendi")

async def addco(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.username != data["founder"]:
        return

    user = context.args[0].replace("@", "")

    if user not in data["cofounders"]:
        data["cofounders"].append(user)
        save(data)

    await update.message.reply_text("Yardımcı kurucu eklendi")

# =====================
# BAN
# =====================

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_staff(update.effective_user.username):
        return

    user = context.args[0].replace("@", "")

    await update.message.reply_text(f"{user} banlandı")

# =====================
# UNBAN
# =====================

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_staff(update.effective_user.username):
        return

    user = context.args[0].replace("@", "")

    await update.message.reply_text(f"{user} ban kaldırıldı")

# =====================
# MUTE
# =====================

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_staff(update.effective_user.username):
        return

    user = context.args[0].replace("@", "")

    if user not in data["muted"]:
        data["muted"].append(user)
        save(data)

    await update.message.reply_text(f"{user} mute atıldı")

# =====================
# UNMUTE
# =====================

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_staff(update.effective_user.username):
        return

    user = context.args[0].replace("@", "")

    if user in data["muted"]:
        data["muted"].remove(user)
        save(data)

    await update.message.reply_text(f"{user} mute kaldırıldı")

# =====================
# KICK
# =====================

async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_staff(update.effective_user.username):
        return

    user = context.args[0].replace("@", "")

    await update.message.reply_text(f"{user} kicked")

# =====================
# RUN
# =====================

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("panel", panel))
app.add_handler(CommandHandler("staff", staff))

app.add_handler(CommandHandler("addadmin", addadmin))
app.add_handler(CommandHandler("addmod", addmod))
app.add_handler(CommandHandler("addco", addco))

app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("unban", unban))
app.add_handler(CommandHandler("mute", mute))
app.add_handler(CommandHandler("unmute", unmute))
app.add_handler(CommandHandler("kick", kick))

print("BOT AKTİF")
app.run_polling()
