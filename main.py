import logging
import asyncio
import time
from telethon import TelegramClient, events
from telethon.tl.functions.channels import EditBannedRequest, GetParticipantsRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantsRecent, ChannelParticipantsSearch
from telethon.errors import FloodWaitError

# --- AYARLAR ---
API_ID = 33188452
API_HASH = 'ac4afbd122081956a173b16590c02609'
BOT_TOKEN = '8677463032:AAFPyqqEh3lya4E9_kNlqWYE_XODLq_pIIw'   

BOT_NAME = "ÂrestaXL '"
BOT_SAHIPLERI = [8616625872]   

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

client = TelegramClient('jun_max_session', API_ID, API_HASH)
client.flood_sleep_threshold = 0

logging.basicConfig(level=logging.ERROR)
ban_active = False

@client.on(events.NewMessage(pattern='/x'))
async def god_mode_ban(event):
    global ban_active
    if event.sender_id not in BOT_SAHIPLERI:
        return
    if ban_active:
        await event.respond("⏳ Zaten bir ban işlemi devam ediyor.")
        return

    ban_active = True
    baslangic_zamani = time.time()
    toplam_ban = 0
    ban_sayaci_lock = asyncio.Lock()

    try:
        cmd = event.message.text.split()
        if len(cmd) < 2:
            await event.respond("❌ Kullanım: `/x @grupadı 10000`")
            ban_active = False
            return
        
        chat_username = cmd[1]
        limit = int(cmd[2]) if len(cmd) > 2 else None
        
        chat = await client.get_entity(chat_username)
    except Exception as e:
        await event.respond(f"❌ Grup bulunamadı: {e}")
        ban_active = False
        return

    await event.respond(f"🔍 **Tarama başlatıldı**\nGrup: **{chat.title}**\nTüm üyeler taranıyor...")

    # Kuyruk ve işçiler
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

    # === EN EFSANE TARAMA - BÜTÜN ÜYELERİ ÇEK ===
    members = set()
    try:
        search_chars = [
            '', *list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'),
            'ç','Ç','ğ','Ğ','ı','İ','ö','Ö','ş','Ş','ü','Ü','_','-','.'
        ]

        # Pass 1-3: Geniş arama
        for q in search_chars:
            offset = 0
            while len(members) < 45000:
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
                await asyncio.sleep(0.002)

        # Pass 4+: Recent (pasif ve yeni üyeler için)
        for _ in range(5):
            offset = 0
            while len(members) < 45000:
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
                await asyncio.sleep(0.003)
    except Exception as e:
        await event.respond(f"⚠ Tarama hatası: {e}\nMevcut {len(members)} üyeyle devam ediliyor...")

    member_list = list(members)
    total_members = len(member_list)
    if limit is None or limit > total_members:
        limit = total_members

    await event.respond(f"✅ Tarama tamamlandı.\nToplam üye: **{total_members}**\nBanlanacak: **{limit}** üye\nBan başlıyor...")

    for user_id in member_list[:limit]:
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
    print("🚀 Jun Max Ban Botu çalışıyor...")
    await client.run_until_disconnected()

asyncio.run(main())
