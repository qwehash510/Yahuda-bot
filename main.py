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
BOT_TOKEN = '8689466345:AAGmOlrnMCq_vplCGnGFgCrTC0PbUCZE_mI'   # Burayı kendi bot token'ınla tamamla

BOT_NAME = "Jun"

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
            await event.respond("❌ **Kullanım:** `/x @grupadı 10000`\nSayı girmezsen **tüm üyeleri** banlar.")
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

    await event.respond(f"🔍 **{BOT_NAME} grubu tarıyor...**\nGrup: **{chat.title}**\nLütfen bekleyin...")

    # === ÖNCE TAM TARAMA ===
    members = []
    try:
        async for user in client.iter_participants(chat):
            if not user.bot and not user.is_self and not user.participant.admin_rights and not user.participant.banned_rights:
                members.append(user.id)
        
        total_members = len(members)
        if limit is None:
            limit = total_members
        else:
            limit = min(limit, total_members)
        
        await event.respond(f"🚀 **Tarama tamamlandı!**\nToplam normal üye: **{total_members}**\nBanlanacak: **{limit}** üye\n**{BOT_NAME} şimdi banlamaya başlıyor...**")
    except Exception as e:
        await event.respond(f"⚠ **Tarama hatası:** {e}\nDevam ediyorum...")
        members = []
        limit = 0

    # Kuyruk
    queue = asyncio.Queue(maxsize=CONCURRENT_BANS * 2)

    # İşçi
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

    # İlk 'limit' kadar üyeyi kuyruğa ekle
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
        f"Süre: **{gecen_sure:.1f}** saniye\n"
        f"**Kuralsız mod** ile çalıştı."
    )

    ban_active = False


print(f"🚀 **{BOT_NAME}** ULTRA MAX HIZ ile başlatılıyor (ÇOK RİSKLİ)...")
client.start(bot_token=BOT_TOKEN)
client.run_until_disconnected()
