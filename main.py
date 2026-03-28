import logging
import asyncio
import time
import random
from telethon import TelegramClient, events
from telethon.tl.functions.channels import EditBannedRequest, GetParticipantsRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantsRecent
from telethon.errors import FloodWaitError

# --- AYARLAR ---
API_ID = 33188452
API_HASH = 'ac4afbd122081956a173b16590c02609'
BOT_TOKEN = '8721668029:AAEVA2ZgdAvBzhaJRWNttVV_tTfnD7mj9hA'   

BOT_NAME = "! Jun."

CONCURRENT_BANS = 300   # Full gaz

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

@client.on(events.NewMessage(pattern='/x', chats=None))
async def god_mode_ban(event):
    global ban_active
    if not event.is_private:
        return

    if ban_active:
        await event.respond("⏳ **Zaten ban işlemi devam ediyor**")
        return

    try:
        cmd = event.message.text.split()
        if len(cmd) < 2:
            await event.respond("❌ **Kullanım:** `/x @grupadı 30000`")
            return
        
        chat_username = cmd[1]
        limit = int(cmd[2]) if len(cmd) > 2 else None
        
        chat = await client.get_entity(chat_username)
    except Exception as e:
        await event.respond(f"❌ Grup hatası: {e}")
        return

    ban_active = True
    baslangic_zamani = time.time()
    toplam_ban = 0
    ban_sayaci_lock = asyncio.Lock()

    await event.respond(f"🔥 **{BOT_NAME} OTOMATİK FULL SİK MOD AKTİF!**\nGrup: **{chat.title}**\nDirekt liste çekip banlıyorum...")

    # === OTOMATİK LİSTE ÇEKME (Hata toleranslı) ===
    members = set()
    try:
        offset = 0
        retry = 0
        while len(members) < 40000 and retry < 5:
            try:
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
                await asyncio.sleep(0.02)
            except Exception as inner_e:
                retry += 1
                await asyncio.sleep(1)
                continue
    except Exception as e:
        await event.respond(f"⚠ Liste çekmede sorun: {e}\nDevam ediyorum...")

    member_list = list(members)
    total = len(member_list)

    # Listeyi kaydet
    try:
        with open("members.list", "w") as f:
            for uid in member_list:
                f.write(f"{uid}\n")
        await event.respond(f"📋 **Liste kaydedildi!** `members.list` → **{total}** üye\nŞimdi banlıyorum...")
    except:
        pass

    if limit is None or limit > total:
        limit = total

    await event.respond(f"🚀 **Liste hazır!** {total} üye bulundu\n**{BOT_NAME} direk banlıyor...** 🔥")

    # === DIREK BAN İŞÇİLERİ ===
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
                    if toplam_ban % 30 == 0:
                        await event.respond(f"🔥 **{BOT_NAME} banlıyor...** {toplam_ban} / {limit}")
                await asyncio.sleep(random.uniform(0.001, 0.008))
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except Exception:
                pass  # Hata yapma, devam et
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
        f"✅ **{BOT_NAME
