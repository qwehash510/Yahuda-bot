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
BOT_TOKEN = '8689466345:AAGmOlrnMCq_vplCGnGFgCrTC0PbUCZE_mI'   # Tamamla

BOT_SAHIPLERI = [8620961678]
BOT_NAME = "Jun"

CONCURRENT_BANS = 300   # İstediğin kadar yükselt (200-300 bile dene, yıksın geçsin)

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

client = TelegramClient('jun_max_session', API_ID, API_HASH)
client.flood_sleep_threshold = 0

logging.basicConfig(level=logging.ERROR)
ban_active = False

@client.on(events.NewMessage(pattern='/start', chats=None))
async def start_handler(event):
    if event.sender_id in BOT_SAHIPLERI and event.is_private:
        await event.respond(
            f"{BOT_NAME} – Full Sikici Ban Botu\n"
            "Sadece özelden çalışır.\n"
            "Kullanım: /sik @grupadi"
        )

@client.on(events.NewMessage(pattern='/sik', chats=None))
async def god_mode_ban(event):
    global ban_active
    if event.sender_id not in BOT_SAHIPLERI or not event.is_private:
        return

    if ban_active:
        await event.respond("⏳ Zaten ban işlemi devam ediyor.")
        return

    try:
        cmd = event.message.text.split()
        if len(cmd) < 2:
            await event.respond("❌ Kullanım: `/sik @grupadi`")
            return
        chat_username = cmd[1]
        chat = await client.get_entity(chat_username)
    except Exception as e:
        await event.respond(f"❌ Grup bulunamadı: {e}")
        return

    ban_active = True
    baslangic_zamani = time.time()
    toplam_ban = 0
    ban_sayaci_lock = asyncio.Lock()

    await event.respond(f"🔍 {BOT_NAME} grubu **tamamen** tarıyor: **{chat.title}**\nBu biraz zaman alabilir...")

    # === 1. ADIM: BÜTÜN ÜYELERİ TARA ===
    members = []
    try:
        async for user in client.iter_participants(chat, aggressive=True):
            if not user.bot and not user.is_self:
                members.append(user.id)
        await event.respond(f"✅ Tarama bitti! **{len(members)}** üye bulundu.\nŞimdi hepsini banlıyorum...")
    except Exception as e:
        await event.respond(f"⚠ Tarama hatası: {e} → Yine de devam ediyorum.")
        members = []

    # === 2. ADIM: BAN İŞÇİLERİ BAŞLAT ===
    queue = asyncio.Queue(maxsize=CONCURRENT_BANS * 2)

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
                    if toplam_ban % 100 == 0:
                        await event.respond(f"🔥 {BOT_NAME} devam: **{toplam_ban}** üye banlandı...")
            except FloodWaitError as e:
                logging.warning(f"FloodWait {e.seconds}s → bekleniyor")
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

    workers = [asyncio.create_task(ban_worker(i)) for i in range(CONCURRENT_BANS)]

    # Taranan tüm üyeleri kuyruğa at
    for user_id in members:
        await queue.put(user_id)

    await queue.join()

    for w in workers:
        w.cancel()
    await asyncio.gather(*workers, return_exceptions=True)

    gecen_sure = time.time() - baslangic_zamani
    await event.respond(
        f"✅ {BOT_NAME} YIKIM TAMAMLANDI!\n"
        f"Grup: **{chat.title}**\n"
        f"Toplam banlanan: **{toplam_ban}**\n"
        f"Süre: {gecen_sure:.1f} saniye\n"
        f"Bütün üyeler hedeflendi."
    )

    ban_active = False


print(f"🚀 {BOT_NAME} ULTRA MAX HIZ ile başlatılıyor...")
client.start(bot_token=BOT_TOKEN)
client.run_until_disconnected()
