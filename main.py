import logging
import asyncio
import time
from telethon import TelegramClient, events
from telethon.tl.functions.channels import EditBannedRequest, GetParticipantsRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantsRecent, ChannelParticipantsSearch
from telethon.errors import FloodWaitError

# --- AYARLAR ---
API_ID = 33188452
API_HASH = ''                    # Buraya kendi API_HASH'ini yaz
BOT_TOKEN = '8689466345:AAGmOlrnMCq_vplCGnGFgCrTC0PbUCZE_mI'        # Buraya kendi bot tokenini yaz

BOT_SAHIPLERI = [8620961678]

CONCURRENT_BANS = 300

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

client = TelegramClient('bot_session_max', API_ID, API_HASH)
client.flood_sleep_threshold = 0

logging.basicConfig(level=logging.ERROR)
ban_active = False

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.sender_id in BOT_SAHIPLERI:
        await event.respond(
            "Avustralyakrallik Sikici Ban Botu\n"
            "EN KALİTELİ + EN TAM TARAMA MODU\n"
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

    ban_active = True
    baslangic_zamani = time.time()
    toplam_ban = 0
    ban_sayaci_lock = asyncio.Lock()

    try:
        chat = await event.get_chat()
    except:
        await event.respond("❌ Grup alınamadı.")
        ban_active = False
        return

    queue = asyncio.Queue(maxsize=CONCURRENT_BANS * 4)

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
                await asyncio.sleep(e.seconds)
                try:
                    await client(EditBannedRequest(chat, user_id, BAN_RIGHTS))
                    async with ban_sayaci_lock:
                        toplam_ban += 1
                except:
                    pass
            except Exception:
                pass
            finally:
                queue.task_done()

    workers = [asyncio.create_task(ban_worker(i)) for i in range(CONCURRENT_BANS)]

    # === EN KALİTELİ + EN TAM TARAMA ===
    members = set()
    try:
        search_chars = ['', 'a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z',
                        'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
                        '0','1','2','3','4','5','6','7','8','9','ç','Ç','ğ','Ğ','ı','İ','ö','Ö','ş','Ş','ü','Ü','_','-','.']

        # Katman 1: Geniş Arama (isim bazlı)
        for q in search_chars:
            offset = 0
            while len(members) < 400000:
                participants = await client(GetParticipantsRequest(
                    channel=chat,
                    filter=ChannelParticipantsSearch(q),
                    offset=offset,
                    limit=200,
                    hash=0
                ))
                if not participants.users:
                    break
                for p in participants.users:
                    if not getattr(p, 'is_self', False):
                        members.add(p.id)
                offset += len(participants.users)
                await asyncio.sleep(0.003)

        # Katman 2: Recent Pass (pasif + yeni üyeler için) - 4 kez
        for _ in range(4):
            offset = 0
            while len(members) < 400000:
                participants = await client(GetParticipantsRequest(
                    channel=chat,
                    filter=ChannelParticipantsRecent(),
                    offset=offset,
                    limit=200,
                    hash=0
                ))
                if not participants.users:
                    break
                for p in participants.users:
                    if not getattr(p, 'is_self', False):
                        members.add(p.id)
                offset += len(participants.users)
                await asyncio.sleep(0.004)

        # Katman 3: Ekstra offset reset ile tekrar arama (kaçan üyeleri yakalamak için)
        for q in ['', 'a', 'e', 'i', 'o', 'u']:
            offset = 0
            while len(members) < 400000:
                participants = await client(GetParticipantsRequest(
                    channel=chat,
                    filter=ChannelParticipantsSearch(q),
                    offset=offset,
                    limit=200,
                    hash=0
                ))
                if not participants.users:
                    break
                for p in participants.users:
                    if not getattr(p, 'is_self', False):
                        members.add(p.id)
                offset += len(participants.users)
                await asyncio.sleep(0.003)

    except Exception as e:
        logging.error(f"Tarama hatası: {e}")

    # Kuyruğa tüm bulunan üyeleri ekle
    for user_id in members:
        await queue.put(user_id)

    await queue.join()

    for w in workers:
        w.cancel()
    await asyncio.gather(*workers, return_exceptions=True)

    gecen_sure = time.time() - baslangic_zamani

    await event.respond(
        f"✅ İşlem Tamamlandı (EN KALİTELİ + EN TAM TARAMA)\n"
        f"Süre: {gecen_sure:.1f} saniye.\n"
        f"Tarama: {len(members)} üye\n"
        f"Toplam Ban: {toplam_ban}"
    )

    ban_active = False


async def main():
    await client.start(bot_token=BOT_TOKEN)
    print("🚀 Avustralyakrallik Sikici Ban Botu (EN KALİTELİ + EN TAM TARAMA) çalışıyor...")
    await client.run_until_disconnected()

asyncio.run(main())
