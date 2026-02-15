import os
import json
import logging
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
OWNER_ID = int(os.getenv("OWNER_ID"))

ROLES_FILE = "roles.json"

logging.basicConfig(level=logging.INFO)

# ================= LOAD ROLES =================

def load_roles():
    if not os.path.exists(ROLES_FILE):
        with open(ROLES_FILE,"w") as f:
            json.dump({}, f)
    with open(ROLES_FILE) as f:
        return json.load(f)

def save_roles(data):
    with open(ROLES_FILE,"w") as f:
        json.dump(data,f)

roles = load_roles()

# ================= HELPERS =================

def get_role(user_id):
    if str(user_id) == str(OWNER_ID):
        return "owner"
    return roles.get(str(user_id),"user")

def is_staff(user_id):
    return get_role(user_id) in ["owner","coowner","admin","mod"]

def is_admin(user_id):
    return get_role(user_id) in ["owner","coowner","admin"]

def is_owner(user_id):
    return get_role(user_id) == "owner"

# username to id
async def username_to_id(update, context):
    if not context.args:
        return None
    username = context.args[0].replace("@","")

    admins = await update.effective_chat.get_administrators()
    for admin in admins:
        if admin.user.username == username:
            return admin.user.id
    return None

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    await update.message.reply_text(
        "YAHUDA #KABİLE BOT AKTIF\n"
        "Full Staff + Koruma sistemi hazır"
    )

# ================= STAFF =================

async def staff(update,context):

    txt="STAFF LIST\n\n"

    txt+=f"Kurucu: {OWNER_ID}\n"

    for uid,role in roles.items():
        txt+=f"{role.upper()} → {uid}\n"

    await update.message.reply_text(txt)

# ================= ROLE GIVE =================

async def give_coowner(update,context):

    if not is_owner(update.effective_user.id):
        return

    uid = await username_to_id(update,context)
    if not uid:
        return await update.message.reply_text("Kullanıcı bulunamadı")

    roles[str(uid)]="coowner"
    save_roles(roles)

    await update.message.reply_text("Yardımcı kurucu verildi")

async def give_admin(update,context):

    if not is_admin(update.effective_user.id):
        return

    uid = await username_to_id(update,context)

    roles[str(uid)]="admin"
    save_roles(roles)

    await update.message.reply_text("Admin verildi")

async def give_mod(update,context):

    if not is_admin(update.effective_user.id):
        return

    uid = await username_to_id(update,context)

    roles[str(uid)]="mod"
    save_roles(roles)

    await update.message.reply_text("Mod verildi")

# ================= REMOVE =================

async def remove_role(update,context):

    if not is_admin(update.effective_user.id):
        return

    uid = await username_to_id(update,context)

    if str(uid) in roles:
        del roles[str(uid)]
        save_roles(roles)

    await update.message.reply_text("Yetki alındı")

# ================= BAN =================

async def ban(update,context):

    if not is_staff(update.effective_user.id):
        return

    uid = await username_to_id(update,context)

    await context.bot.ban_chat_member(update.effective_chat.id, uid)

    await update.message.reply_text("Banlandı")

# ================= UNBAN =================

async def unban(update,context):

    if not is_staff(update.effective_user.id):
        return

    uid = await username_to_id(update,context)

    await context.bot.unban_chat_member(update.effective_chat.id, uid)

    await update.message.reply_text("Ban kaldırıldı")

# ================= MUTE =================

async def mute(update,context):

    if not is_staff(update.effective_user.id):
        return

    uid = await username_to_id(update,context)

    perms = ChatPermissions(can_send_messages=False)

    await context.bot.restrict_chat_member(update.effective_chat.id, uid, perms)

    await update.message.reply_text("Mute atıldı")

# ================= UNMUTE =================

async def unmute(update,context):

    if not is_staff(update.effective_user.id):
        return

    uid = await username_to_id(update,context)

    perms = ChatPermissions(can_send_messages=True)

    await context.bot.restrict_chat_member(update.effective_chat.id, uid, perms)

    await update.message.reply_text("Mute kaldırıldı")

# ================= LINK PROTECT =================

anti_link=True

async def link_protect(update,context):

    if not anti_link:
        return

    if is_staff(update.effective_user.id):
        return

    txt=update.message.text

    if "http" in txt or "t.me" in txt:

        await update.message.delete()

# ================= MAIN =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("staff", staff))

app.add_handler(CommandHandler("coowner", give_coowner))
app.add_handler(CommandHandler("admin", give_admin))
app.add_handler(CommandHandler("mod", give_mod))

app.add_handler(CommandHandler("yetkial", remove_role))

app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("unban", unban))
app.add_handler(CommandHandler("mute", mute))
app.add_handler(CommandHandler("unmute", unmute))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, link_protect))

print("BOT AKTIF")

app.run_polling()
