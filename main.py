import logging
import asyncio
import time
from telethon import TelegramClient, events
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights
from telethon.errors import FloodWaitError

# --- AYARLAR ---
API_ID = 33188452
API_HASH = 'ac4afbd122081956a173b16590c02609'
BOT_TOKEN = '8721668029:AAEVA2ZgdAvBzhaJRWNttVV_tTfnD7mj9hA'   # Burayı kendi bot token'ınla tamamla

BOT_NAME = "! Jun."

# AYNI ANDA ÇALIŞACAK YASAKLAMA İŞÇİ SAYISI (ULTRA MAX İÇİN 100)
CONCURRENT_BANS = 300

# Yasaklama hakları (tüm yetkiler kısıtlanır)
BAN_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True,
    send_polls=True,
    change_info=True,
    invite_users=True,
    pin_messages=True
)

# İstemci oluştur
client = TelegramClient('jun_max_session', API_ID, API_HASH)

# Flood korumasını tamamen kaldır (riskli, ultra hız için)
client.flood_sleep_threshold = 0

logging.basicConfig(level=logging.ERROR)
ban_active = False

@client.on(events.NewMessage(pattern='/x', chats=None))
async def god_mode_ban(event):
    global ban_active
    if not event.is_private:
        return

    if ban_active:
        await event.respond("⏳ **Zaten bir ban işlemi devam ediyor**, lütfen bekleyin.")
        return

    try:
        cmd = event.message.text.split()
        if len(cmd) < 2:
            await event.respond("❌ **Kullanım:** `/x @grupadı 10000`\nSayı girmezsen **tüm normal üyeleri** banlar.")
            return
        
        chat_username = cmd[1]
        limit = int(cmd[2]) if len(cmd) > 2 else None
        
        chat = await client.get_entity(chat_username)
    except ValueError:
        await event.respond("❌ **Limit sayı olmalı!** Örnek: `/x @grupadı 10000`")
        return
    except Exception as e:
        await event.respond(f"❌ **Grup bulunamadı** veya hata: {e}")
        return

    ban_active = True
    baslangic_zamani = time.time()
    toplam_ban = 0
    ban_sayaci_lock = asyncio.Lock()

    await event.respond(f"🔥 **{BOT_NAME} DELİ DEHŞET TARAMA MODU AKTİF!**\nGrup: **{chat.title}**\n**Kuralsız manyak hız** ile tarıyorum...")

    # === DELİ DEHŞET KURALSIZ TARAMA ===
    members = []
    try:
        # aggressive=True + limit=None ile en hızlı ve en tam tarama (Telegram limitlerini zorla)
        async for user in client.iter_participants(chat, aggressive=True, limit=None):
            if not user.bot and not user.is_self and not getattr(user.participant, 'admin_rights', None) and not getattr(user.participant, 'banned_rights', None):
                members.append(user.id)
        
        total_members = len(members)
        if limit is None or limit > total_members:
            limit = total_members
        
        await event.respond(f"🚀 **DEHŞET TARAMA BİTTİ!**\nToplam normal üye: **{total_members}**\nBanlanacak: **{limit}** üye\n**{BOT_NAME} şimdi full gaz banlıyor...** 🔥🔥🔥")
    except Exception as e:
        await event.respond(f"⚠ **Tarama hatası:** {e}\nYine de devam ediyorum...")
        members = []
        limit = 0

    # Kuyruk
    queue = asyncio.Queue(maxsize=CONCURRENT_BANS * 2)

    # İşçi (ban kısmı hiç değişmedi)
    async def ban_worker(worker_id):
        nonlocal toplam_ban
        while True:
            try:
                user_id = await queue.get()
            except asyncio.CancelledError:
                break

            try:
                await client(EditBannedRequest(chat, user_id, BAN_RIGHTS))
                async with ban_sayaci_lock:
                    toplam_ban += 1
                    if toplam_ban % 50 == 0:
                        await event.respond(f"🔥 **{BOT_NAME} devam ediyor...**\nBanlanan: **{toplam_ban}** / {limit}")
            except FloodWaitError as e:
                logging.warning(f"FloodWait {e.seconds} saniye")
                await asyncio.sleep(e.seconds)
                try:
                    await client(EditBannedRequest(chat, user_id, BAN_RIGHTS))
                    async with ban_sayaci_lock:
                        toplam_ban += 1
                except:
                    pass
            except Exception as e:
                logging.error(f"Ban hatası (ID: {user_id}): {e}")
            finally:
                queue.task_done()

    # İşçileri başlat
    workers = [asyncio.create_task(ban_worker(i)) for i in range(CONCURRENT_BANS)]

    # Taranan üyeleri kuyruğa at (sadece limit kadar)
    for user_id in members[:limit]:
        await queue.put(user_id)

    await queue.join()

    for w in workers:
        w.cancel()
    await asyncio.gather(*workers, return_exceptions=True)

    gecen_sure = time.time() - baslangic_zamani
    await event.respond(
        f"✅ **{BOT_NAME} YIKIM TAMAMLANDI!**\n"
        f"Grup: **{chat.title}**\n"
        f"Toplam Ban: **{toplam_ban}** / {limit}\n"
    )

    ban_active = False


async def main():
    await client.start(bot_token=BOT_TOKEN)
    print("🚀 Bot çalışıyor...")
    await client.run_until_disconnected()

asyncio.run(main())
