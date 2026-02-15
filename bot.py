import json
import os
import time
import logging
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

STAFF_FILE = "staff.json"
PROTECT_FILE = "protect.json"

# JSON LOAD/SAVE
def load(file, default):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        save(file, default)
        return default

def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# DATA
staff = load(STAFF_FILE,{
    "kurucu":[],
    "yardimci":[],
    "admin":[],
    "mod":[],
    "susturucu":[]
})

protect = load(PROTECT_FILE,{
    "enabled":True,
    "link":True,
    "spam":True
})

spam = {}

# USERNAME FORMAT
def uname(user):
    if user.username:
        return "@"+user.username
    return user.first_name

# GET TARGET USERNAME
def get_target(update):

    args = update.message.text.split()

    if len(args)<2:
        return None

    u=args[1]

    if not u.startswith("@"):
        u="@"+u

    return u

# ROLE CHECK
def is_kurucu(u): return u in staff["kurucu"]

def is_yardimci(u): return u in staff["yardimci"]

def is_admin(u):
    return (
        u in staff["kurucu"] or
        u in staff["yardimci"] or
        u in staff["admin"]
    )

def is_staff(u):

    for r in staff:
        if u in staff[r]:
            return True

    return False

# START
async def start(update,context):

    u=uname(update.effective_user)

    if not staff["kurucu"]:

        staff["kurucu"].append(u)
        save(STAFF_FILE,staff)

        await update.message.reply_text(
            f"👑 {u} Kurucu oldu.\nYAHUDA #KABİLE AKTİF"
        )

    else:

        await update.message.reply_text("Bot aktif.")

# STAFF LIST
async def staff_list(update,context):

    txt="☠️ YAHUDA #KABİLE STAFF\n\n"

    roles={
        "kurucu":"👑 Kurucu",
        "yardimci":"⚜ Yardımcı Kurucu",
        "admin":"🛡 Admin",
        "mod":"🔧 Mod",
        "susturucu":"🔇 Susturucu"
    }

    for r in roles:

        txt+=roles[r]+"\n"

        if staff[r]:

            for u in staff[r]:

                txt+="• "+u+"\n"

        else:

            txt+="• yok\n"

        txt+="\n"

    await update.message.reply_text(txt)

# GIVE ROLE
async def give_role(update,context,role):

    sender=uname(update.effective_user)

    if not (is_kurucu(sender) or is_yardimci(sender)):
        return await update.message.reply_text("Yetkin yok.")

    target=get_target(update)

    if not target:
        return await update.message.reply_text("Kullanım: /komut @username")

    if target not in staff[role]:

        staff[role].append(target)
        save(STAFF_FILE,staff)

    await update.message.reply_text(f"{target} artık {role}")

# ROLE COMMANDS
async def kurucu(update,context): await give_role(update,context,"kurucu")
async def yardimci(update,context): await give_role(update,context,"yardimci")
async def admin(update,context): await give_role(update,context,"admin")
async def mod(update,context): await give_role(update,context,"mod")
async def susturucu(update,context): await give_role(update,context,"susturucu")

# REMOVE ROLE
async def yetkial(update,context):

    sender=uname(update.effective_user)

    if not is_kurucu(sender):
        return

    target=get_target(update)

    if not target:
        return

    for r in staff:

        if target in staff[r]:
            staff[r].remove(target)

    save(STAFF_FILE,staff)

    await update.message.reply_text("Yetki alındı.")

# BAN
async def ban(update,context):

    sender=uname(update.effective_user)

    if not is_admin(sender):
        return

    if update.message.reply_to_message:

        uid=update.message.reply_to_message.from_user.id

        await update.effective_chat.ban_member(uid)

# MUTE
async def mute(update,context):

    sender=uname(update.effective_user)

    if not is_staff(sender):
        return

    if update.message.reply_to_message:

        uid=update.message.reply_to_message.from_user.id

        await update.effective_chat.restrict_member(
            uid,
            ChatPermissions(can_send_messages=False)
        )

# UNMUTE
async def unmute(update,context):

    sender=uname(update.effective_user)

    if not is_staff(sender):
        return

    if update.message.reply_to_message:

        uid=update.message.reply_to_message.from_user.id

        await update.effective_chat.restrict_member(
            uid,
            ChatPermissions(can_send_messages=True)
        )

# PROTECTION
async def protect_msg(update,context):

    if not protect["enabled"]:
        return

    text=update.message.text.lower()

    user=update.effective_user.id

    # LINK BLOCK
    if protect["link"] and ("http" in text or "t.me" in text):

        await update.message.delete()

        return

    # SPAM BLOCK
    now=time.time()

    if user in spam:

        if now-spam[user]<1:

            await update.message.delete()

            return

    spam[user]=now

# PROTECT ON OFF
async def koruma(update,context):

    sender=uname(update.effective_user)

    if not is_kurucu(sender):
        return

    if "aç" in update.message.text:

        protect["enabled"]=True

    else:

        protect["enabled"]=False

    save(PROTECT_FILE,protect)

    await update.message.reply_text("Koruma güncellendi.")

# WELCOME
async def welcome(update,context):

    for user in update.message.new_chat_members:

        await update.message.reply_text(
            f"⚡ YAHUDA #KABİLE\nHoşgeldin @{user.username}"
        )

# BYE
async def bye(update,context):

    user=update.message.left_chat_member

    await update.message.reply_text(
        f"@{user.username} ayrıldı."
    )

# PING
async def ping(update,context):

    await update.message.reply_text("⚡ Bot aktif")

# MAIN
app=ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("staff",staff_list))

app.add_handler(CommandHandler("kurucu",kurucu))
app.add_handler(CommandHandler("yardimci",yardimci))
app.add_handler(CommandHandler("admin",admin))
app.add_handler(CommandHandler("mod",mod))
app.add_handler(CommandHandler("susturucu",susturucu))

app.add_handler(CommandHandler("yetkial",yetkial))

app.add_handler(CommandHandler("ban",ban))
app.add_handler(CommandHandler("mute",mute))
app.add_handler(CommandHandler("unmute",unmute))

app.add_handler(CommandHandler("koruma",koruma))
app.add_handler(CommandHandler("ping",ping))

app.add_handler(MessageHandler(filters.TEXT,protect_msg))

app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS,welcome))
app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER,bye))

print("☠️ YAHUDA #KABİLE EFSANE v6 SUPREME AKTİF")

app.run_polling()
