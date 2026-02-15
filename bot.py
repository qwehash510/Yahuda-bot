import os
import json
import logging
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

ROLES_FILE = "roles.json"
CONFIG_FILE = "config.json"

logging.basicConfig(level=logging.INFO)

# ================= LOAD =================

def load(file, default):

    if not os.path.exists(file):
        with open(file,"w") as f:
            json.dump(default,f)

    with open(file) as f:
        return json.load(f)

def save(file,data):

    with open(file,"w") as f:
        json.dump(data,f)

roles = load(ROLES_FILE,{})
config = load(CONFIG_FILE,{"protect":True})

# ================= ROLE SYSTEM =================

def get_role(uid):

    if uid == OWNER_ID:
        return "👑 Kurucu"

    return roles.get(str(uid),"Üye")

def is_staff(uid):

    return get_role(uid) in [
        "👑 Kurucu",
        "⚜ Yardımcı Kurucu",
        "☠ Admin",
        "⚔ Mod"
    ]

def is_admin(uid):

    return get_role(uid) in [
        "👑 Kurucu",
        "⚜ Yardımcı Kurucu",
        "☠ Admin"
    ]

# ================= USERNAME RESOLVE =================

async def resolve_user(update, context):

    if not context.args:
        return None, None

    username = context.args[0].replace("@","")

    members = await update.effective_chat.get_administrators()

    for m in members:

        if m.user.username == username:

            return m.user.id, "@"+username

    return None, None

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    await update.message.reply_text(
"""
⚡ YAHUDA #KRALLIK SECURITY SYSTEM ⚡

Sistem aktive edildi.

Komutlar:
/panel
/staff
/koruma_ac
"""
)

# ================= PANEL =================

async def panel(update, context):

    if not is_staff(update.effective_user.id):
        return

    await update.message.reply_text(
"""
⚔ YAHUDA HACKER PANEL ⚔

Yetki:
/coowner @user
/admin @user
/mod @user
/yetkial @user

Moderasyon:
/ban @user
/unban @user
/mute @user
/unmute @user
/kick @user

Koruma:
/koruma_ac
/koruma_kapat
"""
)

# ================= STAFF LIST =================

async def staff(update, context):

    txt = "⚔ YAHUDA #KRALLIK STAFF ⚔\n\n"

    chat_admins = await update.effective_chat.get_administrators()

    for admin in chat_admins:

        uid = admin.user.id
        username = admin.user.username

        if username is None:
            continue

        role = get_role(uid)

        if role != "Üye":

            txt += f"{role} → @{username}\n"

        if uid == OWNER_ID:

            txt += f"👑 Kurucu → @{username}\n"

    await update.message.reply_text(txt)

# ================= GIVE ROLE =================

async def coowner(update,context):

    if update.effective_user.id != OWNER_ID:
        return

    uid, username = await resolve_user(update,context)

    if not uid:
        return await update.message.reply_text("Kullanıcı bulunamadı")

    roles[str(uid)]="⚜ Yardımcı Kurucu"
    save(ROLES_FILE,roles)

    await update.message.reply_text(f"{username} yardımcı kurucu yapıldı")

async def admin_cmd(update,context):

    if not is_admin(update.effective_user.id):
        return

    uid, username = await resolve_user(update,context)

    roles[str(uid)]="☠ Admin"
    save(ROLES_FILE,roles)

    await update.message.reply_text(f"{username} admin yapıldı")

async def mod(update,context):

    if not is_admin(update.effective_user.id):
        return

    uid, username = await resolve_user(update,context)

    roles[str(uid)]="⚔ Mod"
    save(ROLES_FILE,roles)

    await update.message.reply_text(f"{username} mod yapıldı")

# ================= REMOVE ROLE =================

async def yetkial(update,context):

    if not is_admin(update.effective_user.id):
        return

    uid, username = await resolve_user(update,context)

    if str(uid) in roles:

        del roles[str(uid)]

        save(ROLES_FILE,roles)

    await update.message.reply_text(f"{username} yetkisi alındı")

# ================= BAN =================

async def ban(update,context):

    if not is_staff(update.effective_user.id):
        return

    uid, username = await resolve_user(update,context)

    await context.bot.ban_chat_member(update.effective_chat.id, uid)

    await update.message.reply_text(f"{username} sistemden silindi ☠")

# ================= UNBAN =================

async def unban(update,context):

    if not is_staff(update.effective_user.id):
        return

    uid, username = await resolve_user(update,context)

    await context.bot.unban_chat_member(update.effective_chat.id, uid)

    await update.message.reply_text(f"{username} tekrar erişim kazandı")

# ================= MUTE =================

async def mute(update,context):

    if not is_staff(update.effective_user.id):
        return

    uid, username = await resolve_user(update,context)

    await context.bot.restrict_chat_member(
        update.effective_chat.id,
        uid,
        ChatPermissions(can_send_messages=False)
    )

    await update.message.reply_text(f"{username} susturuldu")

# ================= UNMUTE =================

async def unmute(update,context):

    if not is_staff(update.effective_user.id):
        return

    uid, username = await resolve_user(update,context)

    await context.bot.restrict_chat_member(
        update.effective_chat.id,
        uid,
        ChatPermissions(can_send_messages=True)
    )

    await update.message.reply_text(f"{username} tekrar konuşabilir")

# ================= KICK =================

async def kick(update,context):

    if not is_staff(update.effective_user.id):
        return

    uid, username = await resolve_user(update,context)

    await context.bot.ban_chat_member(update.effective_chat.id, uid)
    await context.bot.unban_chat_member(update.effective_chat.id, uid)

    await update.message.reply_text(f"{username} kovuldu")

# ================= PROTECT =================

async def koruma_ac(update,context):

    if not is_admin(update.effective_user.id):
        return

    config["protect"]=True
    save(CONFIG_FILE,config)

    await update.message.reply_text("Koruma aktif")

async def koruma_kapat(update,context):

    if not is_admin(update.effective_user.id):
        return

    config["protect"]=False
    save(CONFIG_FILE,config)

    await update.message.reply_text("Koruma kapalı")

# ================= FILTER =================

async def filter_msg(update,context):

    if not config["protect"]:
        return

    if is_staff(update.effective_user.id):
        return

    txt = update.message.text.lower()

    if "http" in txt or "t.me" in txt:

        await update.message.delete()

# ================= MAIN =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("panel",panel))
app.add_handler(CommandHandler("staff",staff))

app.add_handler(CommandHandler("coowner",coowner))
app.add_handler(CommandHandler("admin",admin_cmd))
app.add_handler(CommandHandler("mod",mod))
app.add_handler(CommandHandler("yetkial",yetkial))

app.add_handler(CommandHandler("ban",ban))
app.add_handler(CommandHandler("unban",unban))
app.add_handler(CommandHandler("mute",mute))
app.add_handler(CommandHandler("unmute",unmute))
app.add_handler(CommandHandler("kick",kick))

app.add_handler(CommandHandler("koruma_ac",koruma_ac))
app.add_handler(CommandHandler("koruma_kapat",koruma_kapat))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_msg))

print("YAHUDA SECURITY SYSTEM ACTIVE")

app.run_polling()
