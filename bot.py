import os
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict

from telegram import Update, ChatPermissions
from telegram.ext import (
    Application, CommandHandler,
    MessageHandler, ContextTypes,
    filters, ChatMemberHandler
)

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

FILE = "yahuda.json"

# ================= LOAD =================

def load():
    try:
        with open(FILE) as f:
            return json.load(f)
    except:
        return {
            "kurucu": [],
            "yardimci": [],
            "admin": [],
            "mod": [],
            "susturucu": [],
            "warn": {},
            "koruma": {
                "antispam": True,
                "antilink": True,
                "antikufur": True,
                "antiflood": True,
                "antiraid": True,
                "antibot": True
            }
        }

def save():
    with open(FILE,"w") as f:
        json.dump(data,f,indent=2)

data = load()

# ================= USERNAME =================

def uname(user):
    if user.username:
        return "@"+user.username.lower()
    return user.first_name.lower()

def arg(update):
    try:
        u = update.message.text.split()[1]
        if not u.startswith("@"):
            u="@"+u
        return u.lower()
    except:
        return None

# ================= ROLE CHECK =================

def is_kurucu(u): return u in data["kurucu"]
def is_yardimci(u): return u in data["yardimci"]
def is_admin(u): return u in data["admin"]
def is_mod(u): return u in data["mod"]

def is_staff(u):
    return (
        is_kurucu(u)
        or is_yardimci(u)
        or is_admin(u)
        or is_mod(u)
        or u in data["susturucu"]
    )

# ================= ROLE ADD =================

async def role_add(update, role):

    sender = uname(update.effective_user)

    if not is_kurucu(sender):
        return

    target = arg(update)

    if not target:
        return

    if target not in data[role]:
        data[role].append(target)
        save()

    await update.message.reply_text(f"{target} → {role}")

# ================= ROLE REMOVE =================

async def role_remove(update, role):

    sender = uname(update.effective_user)

    if not is_kurucu(sender):
        return

    target = arg(update)

    if target in data[role]:
        data[role].remove(target)
        save()

        await update.message.reply_text(f"{target} kaldırıldı")

# ================= STAFF =================

async def staff(update, context):

    text="☠️ YAHUDA #KABİLE STAFF ☠️\n\n"

    text+="👑 Kurucu\n"
    for x in data["kurucu"]:
        text+=x+"\n"

    text+="\n⚜ Yardımcı Kurucu\n"
    for x in data["yardimci"]:
        text+=x+"\n"

    text+="\n🛡 Admin\n"
    for x in data["admin"]:
        text+=x+"\n"

    text+="\n🔧 Mod\n"
    for x in data["mod"]:
        text+=x+"\n"

    text+="\n🔇 Susturucu\n"
    for x in data["susturucu"]:
        text+=x+"\n"

    await update.message.reply_text(text)

# ================= PROTECTION =================

KUFUR=["amk","aq","orospu","piç"]
spam=defaultdict(list)

async def protect(update, context):

    if not update.message:
        return

    user=uname(update.effective_user)

    if is_staff(user):
        return

    text=update.message.text.lower()

    chat=update.effective_chat.id

    if data["koruma"]["antilink"]:
        if "http" in text or "t.me" in text:
            await update.message.delete()

    if data["koruma"]["antikufur"]:
        for k in KUFUR:
            if k in text:
                await update.message.delete()

    if data["koruma"]["antispam"]:
        now=datetime.now()

        spam[user].append(now)

        spam[user]=[
            t for t in spam[user]
            if now-t<timedelta(seconds=5)
        ]

        if len(spam[user])>5:

            await context.bot.restrict_chat_member(
                chat,
                update.effective_user.id,
                ChatPermissions(can_send_messages=False),
                until_date=now+timedelta(minutes=10)
            )

# ================= CLEAN =================

async def temizle(update, context):

    if not is_staff(uname(update.effective_user)):
        return

    try:
        n=int(context.args[0])
    except:
        return

    chat=update.effective_chat.id
    msg=update.message.message_id

    for i in range(n):
        try:
            await context.bot.delete_message(chat,msg-i)
        except:
            pass

# ================= PANEL =================

async def panel(update, context):

    text="""
☠️ YAHUDA #KABİLE PANEL ☠️

Staff:
/kurucu
/yardimci
/admin
/mod

Koruma:
/antispam ac/kapat
/antilink ac/kapat
/antikufur ac/kapat

Yönetim:
/ban
/mute
/kick
/temizle
"""

    await update.message.reply_text(text)

# ================= MAIN =================

def main():

    app=Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("kurucu",lambda u,c:role_add(u,"kurucu")))
    app.add_handler(CommandHandler("yardimci",lambda u,c:role_add(u,"yardimci")))
    app.add_handler(CommandHandler("admin",lambda u,c:role_add(u,"admin")))
    app.add_handler(CommandHandler("mod",lambda u,c:role_add(u,"mod")))
    app.add_handler(CommandHandler("susturucu",lambda u,c:role_add(u,"susturucu")))

    app.add_handler(CommandHandler("staff",staff))
    app.add_handler(CommandHandler("panel",panel))
    app.add_handler(CommandHandler("temizle",temizle))

    app.add_handler(MessageHandler(filters.TEXT,protect))

    print("YAHUDA OMEGA SUPREME AKTİF")

    app.run_polling()

if __name__=="__main__":
    main()
