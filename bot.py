import os
import json
import logging
import asyncio
from datetime import datetime, timedelta

from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ChatMemberHandler,
)

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise Exception("BOT_TOKEN bulunamadı!")

DATA_FILE = "data.json"

logging.basicConfig(level=logging.INFO)

# ================= DATABASE =================

def load():
    try:
        with open(DATA_FILE) as f:
            return json.load(f)
    except:
        return {
            "founder": None,
            "co_founders": [],
            "admins": [],
            "mods": [],
            "mutes": [],
            "warns": {},
            "antilink": False,
            "antibot": False,
            "antispam": False,
            "antiraid": False
        }

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load()

# ================= PERMISSION =================

def role(user_id):

    if user_id == db["founder"]:
        return "founder"

    if user_id in db["co_founders"]:
        return "co"

    if user_id in db["admins"]:
        return "admin"

    if user_id in db["mods"]:
        return "mod"

    if user_id in db["mutes"]:
        return "mute"

    return "user"

def is_staff(user_id):

    return role(user_id) in ["founder","co","admin","mod","mute"]

# ================= USERNAME =================

def uname(user):

    if user.username:
        return "@" + user.username
    else:
        return user.full_name

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if db["founder"] is None:

        db["founder"] = user.id
        save(db)

        await update.message.reply_text(
            f"""
╔══════════════╗
👑 YAHUDA #KABİLE
╚══════════════╝

Kurucu atandı:
{uname(user)}
"""
        )

    else:

        await update.message.reply_text(
            "⚡ YAHUDA #KABİLE aktif"
        )

# ================= STAFF =================

async def staff(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = "╔══ STAFF ══╗\n\n"

    chat = update.effective_chat

    if db["founder"]:

        member = await chat.get_member(db["founder"])

        text += f"👑 Kurucu: {uname(member.user)}\n"

    for uid in db["co_founders"]:

        member = await chat.get_member(uid)

        text += f"⚜️ Yardımcı Kurucu: {uname(member.user)}\n"

    for uid in db["admins"]:

        member = await chat.get_member(uid)

        text += f"🛡 Admin: {uname(member.user)}\n"

    for uid in db["mods"]:

        member = await chat.get_member(uid)

        text += f"⚔️ Mod: {uname(member.user)}\n"

    for uid in db["mutes"]:

        member = await chat.get_member(uid)

        text += f"🔇 Susturucu: {uname(member.user)}\n"

    await update.message.reply_text(text)

# ================= ROLE VER =================

async def yetki(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if role(update.effective_user.id) != "founder":
        return

    if not update.message.reply_to_message:
        return

    target = update.message.reply_to_message.from_user

    arg = context.args[0]

    if arg == "co":
        db["co_founders"].append(target.id)
        txt="Yardımcı Kurucu"

    elif arg == "admin":
        db["admins"].append(target.id)
        txt="Admin"

    elif arg == "mod":
        db["mods"].append(target.id)
        txt="Mod"

    elif arg == "mute":
        db["mutes"].append(target.id)
        txt="Susturucu"

    else:
        return

    save(db)

    await update.message.reply_text(
        f"{uname(target)} → {txt} yapıldı"
    )

# ================= BAN =================

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_staff(update.effective_user.id):
        return

    user = update.message.reply_to_message.from_user

    await update.effective_chat.ban_member(user.id)

    await update.message.reply_text(
        f"🔨 {uname(user)} banlandı"
    )

# ================= KICK =================

async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_staff(update.effective_user.id):
        return

    user = update.message.reply_to_message.from_user

    await update.effective_chat.ban_member(user.id)
    await update.effective_chat.unban_member(user.id)

    await update.message.reply_text(
        f"👢 {uname(user)} kicklendi"
    )

# ================= MUTE =================

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_staff(update.effective_user.id):
        return

    user = update.message.reply_to_message.from_user

    permissions = ChatPermissions(can_send_messages=False)

    await update.effective_chat.restrict_member(
        user.id,
        permissions
    )

    await update.message.reply_text(
        f"🔇 {uname(user)} susturuldu"
    )

# ================= UNMUTE =================

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_staff(update.effective_user.id):
        return

    user = update.message.reply_to_message.from_user

    permissions = ChatPermissions(
        can_send_messages=True
    )

    await update.effective_chat.restrict_member(
        user.id,
        permissions
    )

    await update.message.reply_text(
        f"🔊 {uname(user)} susturuldu kaldırıldı"
    )

# ================= WARN =================

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_staff(update.effective_user.id):
        return

    user = update.message.reply_to_message.from_user

    uid=str(user.id)

    if uid not in db["warns"]:
        db["warns"][uid]=0

    db["warns"][uid]+=1

    save(db)

    await update.message.reply_text(
        f"⚠️ {uname(user)} warn aldı ({db['warns'][uid]}/3)"
    )

    if db["warns"][uid]>=3:

        await update.effective_chat.ban_member(user.id)

# ================= ANTILINK =================

async def antilink(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_staff(update.effective_user.id):
        return

    db["antilink"]=not db["antilink"]

    save(db)

    await update.message.reply_text(
        f"AntiLink → {db['antilink']}"
    )

async def msg(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if db["antilink"]:

        if update.message.text:

            if "http" in update.message.text:

                if not is_staff(update.effective_user.id):

                    await update.message.delete()

# ================= JOIN =================

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):

    for user in update.message.new_chat_members:

        await update.message.reply_text(
            f"""
╔══════════════╗
⚡ HOŞ GELDİN
{uname(user)}
YAHUDA #KABİLE
╚══════════════╝
"""
        )

# ================= MAIN =================

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("staff",staff))
    app.add_handler(CommandHandler("yetki",yetki))
    app.add_handler(CommandHandler("ban",ban))
    app.add_handler(CommandHandler("kick",kick))
    app.add_handler(CommandHandler("mute",mute))
    app.add_handler(CommandHandler("unmute",unmute))
    app.add_handler(CommandHandler("warn",warn))
    app.add_handler(CommandHandler("antilink",antilink))

    app.add_handler(MessageHandler(filters.TEXT,msg))

    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            join
        )
    )

    print("YAHUDA #KABİLE AKTİF")

    app.run_polling()

if __name__ == "__main__":
    main()
