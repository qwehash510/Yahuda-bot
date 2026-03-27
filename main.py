import logging
import asyncio
import time
from telethon import TelegramClient, events
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights
from telethon.errors import FloodWaitError

# --- AYARLAR ---
API_ID = 33188452
API_HASH = ac4afbd122081956a173b16590c02609
BOT_TOKEN = ''
BOT_SAHIPLERI = [8620961678]

# AYNI ANDA ÇALIŞACAK YASAKLAMA İŞÇİ SAYISI (ULTRA MAX İÇİN 100)
CONCURRENT_BANS = 100

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
client = TelegramClient('bot_session_max', API_ID, API_HASH)

# Flood korumasını tamamen kaldır (riskli, ultra hız için)
client.flood_sleep_threshold = 0

logging.basicConfig(level=logging.ERROR)
ban_active = False

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.sender_id in BOT_SAHIPLERI:
        await event.respond(
            "Avustralyakrallik Sikici Ban Botu (MAX HIZ)\n"
            "Sahibim @xDeoddorant & @vesvese."
        )

@client.on(events.NewMessage(pattern='/sik'))
async def god_mode_ban(event):
    global ban_active
    if event.sender_id not in BOT_SAHIPLERI:
        return
    if ban_active:
        await event.respond("⏳ Zaten bir ban işlemi devam ediyor, lütfen bekleyin.")
        return

    chat = await event.get_chat()
    ban_active = True
    baslangic_zamani = time.time()
    toplam_ban = 0
    ban_sayaci_lock = asyncio.Lock()

    # Kuyruk: üretici üyeleri ekleyecek, işçiler tüketecek
    queue = asyncio.Queue(maxsize=CONCURRENT_BANS * 2)

    # İşçi (consumer) görevi
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
            except FloodWaitError as e:
                logging.warning(f"İşçi {worker_id}: FloodWait {e.seconds} saniye, bekleniyor...")
                await asyncio.sleep(e.seconds)
                # Tekrar dene
                try:
                    await client(EditBannedRequest(chat, user_id, BAN_RIGHTS))
                    async with ban_sayaci_lock:
                        toplam_ban += 1
                except Exception as ex:
                    logging.error(f"İşçi {worker_id}: Tekrar denemede hata (ID: {user_id}): {ex}")
            except Exception as e:
                logging.error(f"İşçi {worker_id}: Ban hatası (ID: {user_id}): {e}")
            finally:
                queue.task_done()

    # Üretici (producer) görevi – üyeleri topla ve kuyruğa ekle
    async def producer():
        try:
            async for user in client.iter_participants(chat):
                if not user.bot and not user.is_self:
                    await queue.put(user.id)
        except Exception as e:
            logging.error(f"Üretici hatası: {e}")

    # İşçileri başlat
    workers = [asyncio.create_task(ban_worker(i)) for i in range(CONCURRENT_BANS)]

    # Üreticiyi başlat
    producer_task = asyncio.create_task(producer())

    # Üreticinin bitmesini bekle
    await producer_task

    # Kuyruğa artık yeni öğe gelmeyeceğini belirt
    await queue.join()

    # İşçileri durdur
    for w in workers:
        w.cancel()
    await asyncio.gather(*workers, return_exceptions=True)

    gecen_sure = time.time() - baslangic_zamani
    await event.respond(
        f"✅ İşlem Tamamlandı Siktim geçtim.\n"
        f"Süre: {gecen_sure:.1f} saniye.\n"
        f"Toplam Ban: {toplam_ban}"
    )

    ban_active = False

async def main():
    await client.start(bot_token=BOT_TOKEN)
    print("🚀 Bot çalışıyor...")
    await client.run_until_disconnected()

asyncio.run(main())
