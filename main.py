import logging
import asyncio
import time
from telethon import TelegramClient, events
from telethon.tl.functions.channels import EditBannedRequest, GetParticipantsRequest, GetFullChannelRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantsSearch
from telethon.errors import FloodWaitError, UserNotParticipantError, ChatAdminRequiredError

# --- AYARLAR ---
API_ID = 
API_HASH = ''
BOT_TOKEN = '8200557187:'
BOT_SAHIPLERI = [8571066107]

# DEHŞET BAN HIZI
CONCURRENT_BANS = 500

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

client = TelegramClient('bot_session_jun_max', API_ID, API_HASH)
client.flood_sleep_threshold = 0

logging.basicConfig(level=logging.ERROR)
ban_active = False
group_cache = {}   # Tarama sonuçlarını sakla

# ====================== /b KOMUTU - GRUP BİLGİLERİNİ TARAYIP GÖSTER ======================
@client.on(events.NewMessage(pattern=r'/b(?:\s+(@?\S+))?'))
async def scan_group_handler(event):
    if event.sender_id not in BOT_SAHIPLERI or not event.is_private:
        return

    args = event.message.message.split()
    if len(args) < 2:
        await event.respond("**Kullanim:** `/b @grupadi`")
        return

    target = args[1]
    try:
        chat = await client.get_entity(target)
    except Exception as e:
        await event.respond(f"**Grup bulunamadi:** {str(e)}")
        return

    if not chat or not hasattr(chat, 'megagroup') or not chat.megagroup:
        await event.respond("**Bu bir supergroup degil.**")
        return

    await event.respond(f"**𝕵𝖚𝖓 𝕭𝖆𝖓 𝕭𝖔𝖙**\n**Tarama basliyor...** {chat.title}")

    try:
        full = await client(GetFullChannelRequest(chat))
        uye_sayisi = full.full_chat.participants_count
        admin_list = []
        creator = "Bilinmiyor"
        bot_sayisi = 0

        for p in full.full_chat.participants:
            if hasattr(p, 'user_id'):
                user = await client.get_entity(p.user_id)
                if p.admin_rights:
                    admin_list.append(f"{user.first_name} (ID: {user.id})")
                if p.user_id == chat.creator_id or (hasattr(user, 'bot') and user.bot):
                    if hasattr(user, 'bot') and user.bot:
                        bot_sayisi += 1
                    if p.user_id == chat.creator_id:
                        creator = f"{user.first_name} (ID: {user.id})"

        group_url = f"https://t.me/{chat.username}" if chat.username else "Yok (private)"

        info_text = (
            f"**𝕵𝖚𝖓 𝕭𝖆𝖓 𝕭𝖔𝖙 - GRUP TARAMA SONUCU**\n\n"
            f"**Grup Adi:** {chat.title}\n"
            f"**Grup ID:** `{chat.id}`\n"
            f"**Link:** {group_url}\n"
            f"**Toplam Uye:** {uye_sayisi}\n"
            f"**Kurucu:** {creator}\n"
            f"**Bot Sayisi:** {bot_sayisi}\n"
            f"**Admin Sayisi:** {len(admin_list)}\n"
            f"**Adminler:** {', '.join(admin_list[:10])}{' ve daha fazla...' if len(admin_list) > 10 else ''}\n\n"
            f"**Tarama tamamlandi.** Simdi /x komutu ile ban baslatabilirsiniz."
        )
        await event.respond(info_text)

        # Cache'e kaydet (sonra /x için kullanacağız)
        group_cache[chat.id] = {
            'chat': chat,
            'all_users': [],
            'total_members': uye_sayisi
        }

    except Exception as e:
        await event.respond(f"**Tarama hatasi:** {str(e)}")


# ====================== /x KOMUTU - BELİRLİ SAYIDA BAN ======================
@client.on(events.NewMessage(pattern=r'/x(?:\s+(@?\S+))?(?:\s+(\d+))?'))
async def ultra_ban_handler(event):
    global ban_active
    if event.sender_id not in BOT_SAHIPLERI or not event.is_private:
        return
    if ban_active:
        await event.respond("**𝕵𝖚𝖓 𝕭𝖆𝖓 𝕭𝖔𝖙**\n**Zaten bir ban firtinasi devam ediyor.**")
        return

    args = event.message.message.split()
    if len(args) < 2:
        await event.respond("**Kullanim:** `/x @grupadi 20000`")
        return

    target = args[1]
    try:
        requested_ban_count = int(args[2]) if len(args) > 2 else 999999999
    except ValueError:
        requested_ban_count = 999999999

    try:
        chat = await client.get_entity(target)
    except Exception as e:
        await event.respond(f"**Grup bulunamadi:** {str(e)}")
        return

    if chat.id not in group_cache:
        await event.respond("**Once /b @grupadi ile tarama yapmalisin.**")
        return

    ban_active = True
    baslangic_zamani = time.time()
    toplam_ban = 0
    ban_sayaci_lock = asyncio.Lock()

    cached = group_cache[chat.id]
    await event.respond(f"**𝕵𝖚𝖓 𝕭𝖆𝖓 𝕭𝖔𝖙**\n**Hedef:** {chat.title}\n**Istenen ban sayisi:** {requested_ban_count}\n**Tarama verileri kullaniliyor...** Ban basliyor.")

    # Üyeleri çek (cache'den başla, eksikse tamamla)
    all_user_ids = cached.get('all_users', [])
    if len(all_user_ids) < requested_ban_count:
        offset = len(all_user_ids)
        limit_per_request = 200
        while len(all_user_ids) < requested_ban_count:
            try:
                participants = await client(GetParticipantsRequest(
                    channel=chat,
                    filter=ChannelParticipantsSearch(''),
                    offset=offset,
                    limit=limit_per_request,
                    hash=0
                ))
                if not participants.users:
                    break
                for user in participants.users:
                    if not user.bot and not user.is_self and user.id not in all_user_ids:
                        all_user_ids.append(user.id)
                        if len(all_user_ids) >= requested_ban_count:
                            break
                offset += len(participants.users)
                if len(participants.users) < limit_per_request:
                    break
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds + 2)
            except Exception:
                break

    # Sadece istenen sayıda banla
    users_to_ban = all_user_ids[:requested_ban_count]

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
                except Exception:
                    pass
            except (UserNotParticipantError, ChatAdminRequiredError):
                pass
            except Exception:
                pass
            finally:
                queue.task_done()

    workers = [asyncio.create_task(ban_worker(i)) for i in range(CONCURRENT_BANS)]

    for user_id in users_to_ban:
        await queue.put(user_id)

    await queue.join()

    for w in workers:
        w.cancel()
    await asyncio.gather(*workers, return_exceptions=True)

    gecen_sure = time.time() - baslangic_zamani
    await event.respond(
        f"**𝕵𝖚𝖓 𝕭𝖆𝖓 𝕭𝖔𝖙**\n**ISLEM BITTI!**\n"
        f"**Sure:** {gecen_sure:.1f} saniye\n"
        f"**Istenen Ban:** {requested_ban_count}\n"
        f"**Basarili Ban:** {toplam_ban}\n"
        f"**Hiz:** 500 concurrent worker - dehset mod"
    )

    ban_active = False

print("🚀 Jun Ban Bot - /b ile tarama + /x ile belirtilen sayida dehset ban baslatiliyor...")
client.start(bot_token=BOT_TOKEN)
client.run_until_disconnected()
