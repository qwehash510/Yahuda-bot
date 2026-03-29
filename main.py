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
BOT_TOKEN = '8689466345:AAHBhKNMyck4eaa9sw_CDWbFDJPuscJyQ-s'   

BOT_NAME = "! Jun."

CONCURRENT_BANS = 300   # Ban hızı için artırıldı

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
    if not event.is_private or ban_active:
        return

    ban_active = True
    baslangic_zamani = time.time()
    toplam_ban = 0
    ban_sayaci_lock = asyncio.Lock()

    try:
        cmd = event.message.text.split()
        if len(cmd) < 2:
            await event.respond("❌ **Kullanım:** `/x @grupadı 10000`\nSayı girmezsen **tüm normal üyeleri** banlar.")
            ban_active = False
            return
        
        chat_username = cmd[1]
        limit = int(cmd[2]) if len(cmd) > 2 else None
        chat = await client.get_entity(chat_username)
    except Exception as e:
        await event.respond(f"❌ **Grup bulunamadı** veya hata: {e}")
        ban_active = False
        return

    # 1. MESAJ - Sadece 1 kez
    await event.respond(f"🎴 **{BOT_NAME} ! Jun.**\nGrup: **{chat.title}**\n** tarıyorum...")

    # === DELİ DEHŞET KURALSIZ GENİŞ TARAMA (100k+ kapasite) ===
    members = set()
    try:
        filters = [ChannelParticipantsRecent(), ChannelParticipantsSearch('')]
        search_chars = ['', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']  # Daha geniş brute force

        for f in filters:
            for q in search_chars:
                offset = 0
                while len(members) < 100000:  # 100k'ya kadar zorla (kuralsız geniş kapasite)
                    participants = await client(GetParticipantsRequest(
                        channel=chat,
                        filter=f if isinstance(f, ChannelParticipantsRecent) else ChannelParticipantsSearch(q),
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
                    await asyncio.sleep(0.01)  # Daha hızlı tarama için düşürüldü
        
        member_list = list(members)
        total_members = len(member_list)
        if limit is None or limit > total_members:
            limit = total_members
        
        # 2. MESAJ - Sadece 1 kez
        await event.respond(f"🚀 **Tarama bitti.**\nToplam normal üye: **{total_members}**\nBanlanacak: **{limit}** üye\n**{BOT_NAME} şimdi full gaz banlıyorum...** 🔥🔥🔥")
    except Exception as e:
        await event.respond(f"⚠ **Tarama hatası:** {e}\nElimdeki üyelerle devam ediyorum...")
        member_list = list(members)
        limit = len(member_list) if limit is None else min(limit, len(member_list))

    # === KURALSIZ ULTRA HIZLI BAN İŞÇİLERİ ===
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
                await asyncio.sleep(random.uniform(0.0001, 0.003))  # Kuralsız ultra hızlı delay
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

    # 3. MESAJ - Sadece 1 kez
    await event.respond(
        f"✅ **{BOT_NAME} Banlama tamamlandı..!**\n"
        f"Grup: **{chat.title}**\n"
        f"Toplam Ban: **{toplam_ban}** / {limit}\n"
        f"Süre: **{gecen_sure:.1f}** saniye"
    )

    ban_active = False


async def main():
    await client.start(bot_token=BOT_TOKEN)
    print("🚀 Bot çalışıyor...")
    await client.run_until_disconnected()

asyncio.run(main())
