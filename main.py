import logging
import asyncio
import time
from telethon import TelegramClient, events
from telethon.tl.functions.channels import EditBannedRequest, GetParticipantsRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantsRecent, ChannelParticipantsSearch
from telethon.errors import FloodWaitError

# --- AYARLAR ---
API_ID = 33188452
API_HASH = 'ac4afbd122081956a173b16590c02609'                    # Buraya kendi API_HASH'ini yaz
BOT_TOKEN = '8689466345:AAGmOlrnMCq_vplCGnGFgCrTC0PbUCZE_mI'        # Buraya kendi bot tokenini yaz

BOT_SAHIPLERI = [8571066107]

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

@client.on(events.NewMessage(pattern='/x'))
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
        cmd = event.message.text.split()
        if len(cmd) < 2:
            await event.respond("❗️ Kullanım: `/x @grupadı 10000`")
            ban_active = False
            return

        chat_username = cmd[1]
        limit = int(cmd[2]) if len(cmd) > 2 else None
        chat = await client.get_entity(chat_username)
    except Exception as e:
        await event.respond(f"❌ Grup alınamadı: {e}")
        ban_active = False
        return

    await event.respond(f"🔍 **Tarama başlatıldı...**\nGrup: **{chat.title}**\nTüm üyeler taranıyor...")

    queue = asyncio.Queue(maxsize=CONCURRENT_BANS * 4)

    # Ban işçisi
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

    # === EN KALİTELİ 4 PASS TARAMA ===
    members = set()

    search_chars = [
        '', 
        *list('abcdefghijklmnopqrstuvwxyz'),
        *list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
        *list('0123456789'),
        'ç','Ç','ğ','Ğ','ı','İ','ö','Ö','ş','Ş','ü','Ü','_','-','.'
    ]

    async def scan_search(q):
        local_members = set()
        offset = 0
        last_count = 0

        while offset < 350000:
            try:
                participants = await client(GetParticipantsRequest(
                    channel=chat,
                    filter=ChannelParticipantsSearch(q),
                    offset=offset,
                    limit=200,
                    hash=0
                ))
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
                continue
            except:
                break

            if not participants.users:
                break

            for p in participants.users:
                if not getattr(p, 'is_self', False):
                    local_members.add(p.id)

            current_count = len(participants.users)
            offset += current_count

            if current_count < 120 or current_count == last_count:
                break

            last_count = current_count
            await asyncio.sleep(0.002)

        return local_members

    # 4 Pass Paralel Tarama
    tasks = []
    for q in search_chars:
        tasks.append(asyncio.create_task(scan_search(q)))

    vowels = ['a','e','i','o','u','A','E','I','O','U']
    for _ in range(3):
        for q in vowels:
            tasks.append(asyncio.create_task(scan_search(q)))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for res in results:
        if isinstance(res, set):
            members.update(res)

    # Recent TARAMA (4 Pass)
    for _ in range(4):
        offset = 0
        last_count = 0
        while offset < 350000:
            try:
                participants = await client(GetParticipantsRequest(
                    channel=chat,
                    filter=ChannelParticipantsRecent(),
                    offset=offset,
                    limit=200,
                    hash=0
                ))
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
                continue
            except:
                break

            if not participants.users:
                break

            for p in participants.users:
                if not getattr(p, 'is_self', False):
                    members.add(p.id)

            current_count = len(participants.users)
            offset += current_count

            if current_count < 100 or current_count == last_count:
                break

            last_count = current_count
            await asyncio.sleep(0.003)

    # Kendi kendini banlamayı önle
    if event.sender_id in members:
        members.remove(event.sender_id)

    total_members = len(members)
    if limit is None or limit > total_members:
        limit = total_members

    await event.respond(f"✅ Tarama tamamlandı.\nToplam bulunan üye: **{total_members}**\nBanlanacak: **{limit}** üye\nBan başlıyor...")

    # Kuyruğa ekle
    for user_id in members:
        await queue.put(user_id)

    await queue.join()

    for w in workers:
        w.cancel()
    await asyncio.gather(*workers, return_exceptions=True)

    gecen_sure = time.time() - baslangic_zamani

    await event.respond(
        f"✅ **Banlama tamamlandı.**\n"
        f"Grup: **{chat.title}**\n"
        f"Toplam Ban: **{toplam_ban}** / {limit}\n"
        f"Süre: **{gecen_sure:.1f}** saniye"
    )

    ban_active = False


async def main():
    await client.start(bot_token=BOT_TOKEN)
    print("🚀 Ban botu çalışıyor... /x @grupadı 10000 komutu aktif")
    await client.run_until_disconnected()

asyncio.run(main())
