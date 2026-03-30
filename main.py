import logging
import asyncio
import time
import random
from telethon import TelegramClient, events
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import ChatBannedRights, InputPeerChannel, InputPeerEmpty
from telethon.errors import FloodWaitError

# --- AYARLAR ---
API_ID = 33188452
API_HASH = 'ac4afbd122081956a173b16590c02609'
BOT_TOKEN = '8689466345:AAFWhAmjXQkS04XKnH5_CMQx87H0PN8DiDs'   

BOT_NAME = "! Jun."
OWNERS = {8620961678}

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

client = TelegramClient('jun_raw_mtproto', API_ID, API_HASH)
client.flood_sleep_threshold = 0

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
ban_active = False
last_command_time = 0

@client.on(events.NewMessage(pattern='/x', chats=None))
async def raw_mtproto_ban(event):
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
            await event.respond("❌ **Kullanım:** `/x @grupadı 10000\n")
            ban_active = False
            return
        
        chat_username = cmd[1]
        limit = int(cmd[2]) if len(cmd) > 2 else None
        chat = await client.get_entity(chat_username)
    except Exception as e:
        await event.respond(f"❌ **Grup bulunamadı** veya hata: {e}")
        ban_active = False
        return

    await event.respond(f"🎴 **{BOT_NAME} **\nGrup: **{chat.title}**\n**tarama başlıyor...**")

    # === RAW MTProto İLE EN AGRESİF TARAMA ===
    members = set()
    try:
        # Raw history + participants kombinasyonu
        offset_id = 0
        for _ in range(50):  # Daha fazla pass
            history = await client(GetHistoryRequest(
                peer=chat,
                offset_id=offset_id,
                offset_date=0,
                add_offset=0,
                limit=100,
                max_id=0,
                min_id=0,
                hash=0
            ))
            if not history.messages:
                break
            for msg in history.messages:
                if msg.from_id:
                    uid = msg.from_id.user_id if hasattr(msg.from_id, 'user_id') else msg.from_id
                    if uid:
                        members.add(uid)
            offset_id = history.messages[-1].id if history.messages else 0
            await asyncio.sleep(0.01)

        # Ekstra participants raw
        offset = 0
        while len(members) < 150000:
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
                if not getattr(p, 'bot', False) and not getattr(p, 'is_self', False):
                    members.add(p.id)
            offset += len(participants.users)
            await asyncio.sleep(0.005)
    except Exception as e:
        logging.error(f"Tarama hatası: {e}")

    member_list = list(members)
    total_members = len(member_list)
    if limit is None or limit > total_members:
        limit = total_members

    await event.respond(f"🚀 **tarama bitti!**\nToplam üye: **{total_members}**\nBanlanacak: **{limit}** üye\n**ban başlıyor...**")

    # === KURALSIZ BAN ===
    queue = asyncio.Queue(maxsize=CONCURRENT_BANS * 3)

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

    for user_id in member_list[:limit]:
        await queue.put(user_id)

    await queue.join()

    for w in workers:
        w.cancel()
    await asyncio.gather(*workers, return_exceptions=True)

    gecen_sure = time.time() - baslangic_zamani

    await event.respond(
        f"✅ **{BOT_NAME} Banlama tamamlandı..!**\n"
        f"Grup: **{chat.title}**\n"
        f"Toplam Ban: **{toplam_ban}** / {limit}\n"
        f"Süre: **{gecen_sure:.1f}** saniye"
    )

    ban_active = False


async def main():
    await client.start(bot_token=BOT_TOKEN)
    print("🚀 Raw MTProto Dehşet Tarama + Kuralsız Ban modu aktif")
    await client.run_until_disconnected()

asyncio.run(main())
