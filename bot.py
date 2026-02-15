import telebot
import os
import json
import time
from telebot.types import ChatPermissions

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

FILE = "data.json"

# yükle
def load():
    try:
        with open(FILE) as f:
            return json.load(f)
    except:
        return {
            "founders": [],
            "cofounders": [],
            "admins": [],
            "mods": [],
            "muters": [],
            "banned": [],
            "protections": {
                "link": False,
                "flood": False,
                "reklam": False,
                "staff": True
            },
            "flood": {}
        }

def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load()

# username
def uname(user):
    return user.username.lower() if user.username else None

# yetki kontrol
def founder(u): return u in data["founders"]
def cofounder(u): return u in data["cofounders"]
def admin(u): return u in data["admins"]
def mod(u): return u in data["mods"]
def muter(u): return u in data["muters"]

def staff(u):
    return founder(u) or cofounder(u) or admin(u) or mod(u) or muter(u)

# AKTİF ET
@bot.message_handler(commands=["santana"])
def santana(m):

    u = uname(m.from_user)

    if not u:
        return bot.reply_to(m,"username gerekli")

    if u not in data["founders"]:
        data["founders"].append(u)
        save(data)

    bot.reply_to(m,"☠ YAHUDA #KRALLIK KURUCU AKTİF")

# STAFF PANEL
@bot.message_handler(commands=["staff"])
def staff_panel(m):

    msg="☠ <b>YAHUDA #KRALLIK STAFF</b>\n\n"

    for r,n in [
        ("founders","Kurucu"),
        ("cofounders","Yardımcı Kurucu"),
        ("admins","Yönetici"),
        ("mods","Mod"),
        ("muters","Susturucu")
    ]:
        if data[r]:
            msg+=f"<b>{n}</b>\n"
            for u in data[r]:
                msg+=f"@{u}\n"
            msg+="\n"

    bot.send_message(m.chat.id,msg)

# YETKİ VER
def add_role(role):

    def func(m):

        u=uname(m.from_user)

        if not staff(u): return

        args=m.text.split()

        if len(args)<2: return

        target=args[1].replace("@","").lower()

        if target not in data[role]:

            data[role].append(target)
            save(data)

            bot.reply_to(m,f"{target} eklendi")

    return func

# YETKİ AL
def del_role(role):

    def func(m):

        u=uname(m.from_user)

        if not staff(u): return

        args=m.text.split()

        if len(args)<2: return

        target=args[1].replace("@","").lower()

        if target in data[role]:

            data[role].remove(target)
            save(data)

            bot.reply_to(m,f"{target} kaldırıldı")

    return func

bot.message_handler(commands=["ykver"])(add_role("cofounders"))
bot.message_handler(commands=["ykal"])(del_role("cofounders"))

bot.message_handler(commands=["adminver"])(add_role("admins"))
bot.message_handler(commands=["adminal"])(del_role("admins"))

bot.message_handler(commands=["modver"])(add_role("mods"))
bot.message_handler(commands=["modal"])(del_role("mods"))

bot.message_handler(commands=["susturucuver"])(add_role("muters"))
bot.message_handler(commands=["susturucual"])(del_role("muters"))

# BAN
@bot.message_handler(commands=["ban"])
def ban(m):

    if not staff(uname(m.from_user)): return

    target=m.text.split()[1].replace("@","")

    bot.ban_chat_member(m.chat.id,target)

# UNBAN
@bot.message_handler(commands=["unban"])
def unban(m):

    if not staff(uname(m.from_user)): return

    target=m.text.split()[1].replace("@","")

    bot.unban_chat_member(m.chat.id,target)

# MUTE
@bot.message_handler(commands=["mute"])
def mute(m):

    if not staff(uname(m.from_user)): return

    target=m.text.split()[1].replace("@","")

    bot.restrict_chat_member(
        m.chat.id,
        target,
        ChatPermissions(can_send_messages=False)
    )

# UNMUTE
@bot.message_handler(commands=["unmute"])
def unmute(m):

    if not staff(uname(m.from_user)): return

    target=m.text.split()[1].replace("@","")

    bot.restrict_chat_member(
        m.chat.id,
        target,
        ChatPermissions(can_send_messages=True)
    )

# TEMİZLE
@bot.message_handler(commands=["temizle"])
def temizle(m):

    if not staff(uname(m.from_user)): return

    n=int(m.text.split()[1])

    for i in range(n):
        try:
            bot.delete_message(m.chat.id,m.message_id-i)
        except:
            pass

# KORUMA KOMUT
@bot.message_handler(commands=["linkkoruma"])
def link_koruma(m):

    if not staff(uname(m.from_user)): return

    arg=m.text.split()[1]

    data["protections"]["link"]=arg=="ac"

    save(data)

    bot.reply_to(m,"Link koruma değişti")

# PANEL
@bot.message_handler(commands=["panel"])
def panel(m):

    if not staff(uname(m.from_user)): return

    p=data["protections"]

    msg=f"""
☠ YAHUDA #KRALLIK PANEL

Link: {p["link"]}
Flood: {p["flood"]}
Reklam: {p["reklam"]}
Staff Koruma: {p["staff"]}
"""

    bot.send_message(m.chat.id,msg)

# KORUMA SİSTEMİ
@bot.message_handler(func=lambda m: True)
def protect(m):

    u=uname(m.from_user)

    if not u: return

    if data["protections"]["link"]:

        if "http" in m.text or "t.me" in m.text:

            if not staff(u):

                bot.delete_message(m.chat.id,m.message_id)

print("YAHUDA KRALLIK AKTİF")
bot.infinity_polling()
