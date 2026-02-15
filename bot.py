import json
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ChatMemberUpdated
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
import os

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

ROLES_FILE = "roles.json"

# Roller yükle
def load_roles():
    try:
        with open(ROLES_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "founder": [],
            "cofounder": [],
            "admin": [],
            "mod": []
        }

# Roller kaydet
def save_roles(data):
    with open(ROLES_FILE, "w") as f:
        json.dump(data, f, indent=4)

roles = load_roles()

# Rol kontrol
def has_permission(username):
    if username in roles["founder"]:
        return True
    if username in roles["cofounder"]:
        return True
    if username in roles["admin"]:
        return True
    return False


# HOŞ GELDİN
@dp.chat_member()
async def welcome(event: ChatMemberUpdated):

    if event.new_chat_member.status == "member":

        user = event.from_user

        text = f"""
<pre>
█▓▒░ YAHUDA #KABİLE ░▒▓█

⚠ Sisteme giriş algılandı
👤 Kullanıcı: @{user.username}

☣ Yetkisiz işlem yasaktır
🛡 Sistem korunuyor

Hoş geldin.
</pre>
"""

        await bot.send_message(event.chat.id, text)


# HOŞÇAKAL
@dp.message(F.left_chat_member)
async def goodbye(message: types.Message):

    user = message.left_chat_member

    text = f"""
<pre>
☠ Sistemden çıkış

👤 @{user.username}

YAHUDA seni izliyor...
</pre>
"""

    await message.answer(text)


# YETKİ VER
@dp.message(Command("yetkiver"))
async def yetki_ver(message: types.Message):

    sender = message.from_user.username

    if not has_permission(sender):
        return await message.reply("Yetkin yok.")

    args = message.text.split()

    if len(args) != 3:
        return await message.reply("Kullanım:\n/yetkiver rol username")

    rol = args[1]
    user = args[2].replace("@", "")

    if rol not in roles:
        return await message.reply("Rol hatalı.")

    roles[rol].append(user)
    save_roles(roles)

    await message.reply(f"{user} artık {rol}")


# YETKİ AL
@dp.message(Command("yetkial"))
async def yetki_al(message: types.Message):

    sender = message.from_user.username

    if not has_permission(sender):
        return await message.reply("Yetkin yok.")

    args = message.text.split()

    rol = args[1]
    user = args[2].replace("@", "")

    if user in roles[rol]:
        roles[rol].remove(user)
        save_roles(roles)

    await message.reply("Yetki alındı.")


# ROL GÖRÜNTÜLE
@dp.message(Command("roller"))
async def roller(message: types.Message):

    text = "<b>YAHUDA YETKİ SİSTEMİ</b>\n\n"

    for rol in roles:
        text += f"<b>{rol.upper()}</b>\n"
        for user in roles[rol]:
            text += f"@{user}\n"
        text += "\n"

    await message.reply(text)


# RAID KORUMA
user_join_times = {}

@dp.chat_member()
async def anti_raid(event: ChatMemberUpdated):

    if event.new_chat_member.status == "member":

        now = asyncio.get_event_loop().time()

        user_join_times.setdefault(event.chat.id, [])
        user_join_times[event.chat.id].append(now)

        recent = [
            t for t in user_join_times[event.chat.id]
            if now - t < 10
        ]

        if len(recent) > 5:

            await bot.send_message(
                event.chat.id,
                "⚠ RAID ALGILANDI\nSistem koruma aktif"
            )


# BAŞLAT
async def main():
    print("YAHUDA aktif")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
