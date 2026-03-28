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
BOT_TOKEN = '8721668029:AAEVA2ZgdAvBzhaJRWNttVV_tTfnD7mj9hA'   

BOT_NAME = "! Jun."

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

logging.basicConfig(level=logging.ERROR)
ban_active = False

@client.on(events.NewMessage(pattern='/x', chats=None))
async def god_mode_ban(event):
    global ban_active
    if not event.is_private:
        return

    if ban_active:
        await event.respond("⏳ **Zaten bir ban işlemi devam ediyor**, lütfen bekleyin.")
        return

    try:
        cmd = event.message.text.split()
        if len(cmd) < 2:
            await event.respond("❌ **Kullanım:** `/x @grupadı 10000`\nSayı girmezsen **tüm normal üyeleri** banlar.")
            return
        
        chat_username = cmd[1]
        limit = int(cmd[2]) if len(cmd) > 2 else None
        
        chat = await client.get_entity(chat_username)
    except Exception as e:
        await event.respond(f"❌ **Grup bulunamadı** veya hata: {e}")
        return

    ban_active = True
    baslangic_zamani = time.time()
    toplam_ban = 0
    ban_sayaci_lock = asyncio.Lock()

    await event.respond(f"🔥 **{BOT_NAME} ! Jun.**\nGrup: **{chat.title}**\n**en hızlı mod** ile tarıyorum...")

    # === YENİ FELAKET TARAMA - 30000+ KAPASİTE + Recent + Brute Search ===
    members = set()  # duplicate önlemek için set
    try:
        filters = [ChannelParticipantsRecent(), ChannelParticipantsSearch('')]
        search_chars = ['', 'a', 'b', 'c', 'd', 'e']  # brute force ekstra üye çekmek için

        for f in filters:
            for q in search_chars:
                offset = 0
                while len(members) < 40000:  # 40k'ya kadar zorla
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
                    
                    if len(members) % 5000 == 0 and len(members) > 0:
                        await event.respond(f"🔄 **Tarama devam...** Şu ana kadar: **{len(members)}** üye")
                    
                    await asyncio.sleep(0.03)  # çok hafif, hızı koru
        
        member_list = list(members)
        total_members = len(member_list)
        if limit is None or limit > total_members:
            limit = total_members
        
        await event.respond(f"🚀 **tarama bitti.**\nToplam normal üye: **{total_members}**\nBanlanacak: **{limit}** üye\n**{BOT_NAME} şimdi full gaz banlıyor...** 🔥🔥🔥")
    except Exception as e:
        await event.respond(f"⚠ **Tarama hatası:** {e}\nElimdeki {len(members)} üyeyle devam ediyorum...")
        member_list = list(members)
        limit = len(member_list) if limit is None else min(limit, len(member_list))

    # Kuyruk ve ban işçileri (hiç değişmedi)
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
                    if toplam_ban % 50 == 0:
                        await event.respond(f"🔥 **{BOT_NAME} devam ediyor...**\nBanlanan: **{toplam_ban}** / {limit}")
            except FloodWaitError as e:
                logging.warning(f"FloodWait {e.seconds} saniye")
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

    for user_id in member_list[:limit]:
        await queue.put(user_id)

    await queue.join()

    for w in workers:
        w.cancel()
    await asyncio.gather(*workers, return_exceptions=True)

    gecen_sure = time.time() - baslangic_zamani
    await event.respond(
        f"✅ **{BOT_NAME} YIKIM TAMAMLANDI!**\n"
        f"Grup: **{chat.title}**\n"
        f"Toplam Ban: **{toplam_ban}** / {limit}\n"

    )

    ban_active = False


async def main():
    await client.start(bot_token=BOT_TOKEN)
    print("🚀 Bot çalışıyor...")
    await client.run_until_disconnected()

asyncio.run(main())
