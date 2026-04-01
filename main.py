import logging
import asyncio
import time
import random
from telethon import TelegramClient, events
from telethon.tl.functions.channels import EditBannedRequest, GetParticipantsRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantsRecent, ChannelParticipantsSearch
from telethon.errors import FloodWaitError

# --- AYARLAR ---
API_ID = 33188452
API_HASH = 'ac4afbd122081956a173b16590c02609'
BOT_TOKEN = '8689466345:AAFWhAmjXQkS04XKnH5_CMQx87H0PN8DiDs'   

BOT_NAME = "! Jun."
OWNERS = {8620961678,7511304654,7594281949,8736336350}

CONCURRENT_BANS = 200

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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
ban_active = False
last_command_time = 0

@client.on(events.NewMessage(pattern='/x', chats=None))
async def god_mode_ban(event):
    global ban_active, last_command_time

    if event.sender_id not in OWNERS:
        return

    current_time = time.time()
    if not event.is_private or ban_active or (current_time - last_command_time < 0.5):
        return

    last_command_time = current_time
    ban_active = True
    baslangic_zamani = time.time()
    toplam_ban = 0
    ban_sayaci_lock = asyncio.Lock()

    try:
        cmd = event.message.text.split()
        if len(cmd) < 2:
            await event.respond("❌ **Kullanım:** `/x @grupadı 10000` \n")
            ban_active = False
            return
        
        chat_username = cmd[1]
        limit = int(cmd[2]) if len(cmd) > 2 else None
        chat = await client.get_entity(chat_username)
    except Exception as e:
        await event.respond(f"❗️ **Grup bulunamadı** veya hata: {e}")
        ban_active = False
        return

    await event.respond(f" ⚛️ **{BOT_NAME} **\nGrup: **{chat.title}**\n**🚀bütün üyeleri tarıyorum.**")

    members = set()
    admins = set()

    try:
        search_chars = ['', 'a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z',
                        'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
                        '0','1','2','3','4','5','6','7','8','9','ç','Ç','ğ','Ğ','ı','İ','ö','Ö','ş','Ş','ü','Ü','_','-','.']

        for q in search_chars:
            offset = 0
            while len(members) < 200000:
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
                        if getattr(getattr(p, 'participant', None), 'admin_rights', None):
                            admins.add(p.id)
                        else:
                            members.add(p.id)
                offset += len(participants.users)
                await asyncio.sleep(0.003)   # Tarama hızı artırıldı

        # Ekstra Recent pass (2 kez)
        for _ in range(2):
            offset = 0
            while len(members) < 200000:
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
                        if getattr(getattr(p, 'participant', None), 'admin_rights', None):
                            admins.add(p.id)
                        else:
                            members.add(p.id)
                offset += len(participants.users)
                await asyncio.sleep(0.004)
    except Exception as e:
        logging.error(f"Tarama hatası: {e}")

    member_list = list(members)
    total_members = len(member_list)
    if limit is None or limit > total_members:
        limit = total_members

    await event.respond(f"🚀 **tarama bitti!**\nToplam üye: **{total_members}**\nAdmin: **{len(admins)}** \nBanlanacak: **{limit}** üye\n**{BOT_NAME}🚀banlıyorum...**")

    # === KURALSIZ BAN İŞÇİLERİ (BÜTÜN TARANAN ÜYELERİ BANLA) ===
    queue = asyncio.Queue(maxsize=CONCURRENT_BANS * 3)

    async def ban_worker(worker_id):
        nonlocal toplam_ban
        while True:
            try:
                user_id = await queue.get()
            except asyncio.CancelledError:
                break

            if user_id in admins:
                queue.task_done()
                continue

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

    for user_id in member_list:
        await queue.put(user_id)

    await queue.join()

    for w in workers:
        w.cancel()
    await asyncio.gather(*workers, return_exceptions=True)

    gecen_sure = time.time() - baslangic_zamani

    await event.respond(
        f"✅ **{BOT_NAME} Banlama tamamlandı..!**\n"
        f"Grup: **{chat.title}**\n"
        f"Toplam Ban: **{toplam_ban}** / {total_members}\n"
        f"Süre: **{gecen_sure:.1f}** saniye"
    )

    ban_active = False


async def main():
    await client.start(bot_token=BOT_TOKEN)
    print("🚀 Bot çalışıyor...")
    await client.run_until_disconnected()

asyncio.run(main())
