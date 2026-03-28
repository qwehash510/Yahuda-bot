import logging
import asyncio
import time
from telethon import TelegramClient, events
from telethon.tl.functions.channels import EditBannedRequest, GetParticipantsRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantsSearch
from telethon.errors import FloodWaitError

# --- AYARLAR ---
API_ID = 33188452
API_HASH = 'ac4afbd122081956a173b16590c02609'
BOT_TOKEN = '8721668029:AAEVA2ZgdAvBzhaJRWNttVV_tTfnD7mj9hA'   

BOT_NAME = "! Jun."

# AYNI ANDA ÇALIŞACAK YASAKLAMA İŞÇİ SAYISI 
CONCURRENT_BANS = 300

# Yasaklama hakları (tüm yetkiler kısıtlanır)
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

# İstemci oluştur
client = TelegramClient('jun_max_session', API_ID, API_HASH)

# Flood korumasını tamamen kaldır (riskli, ultra hız için)
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
    except ValueError:
        await event.respond("❌ **Limit sayı olmalı!** Örnek: `/x @grupadı 10000`")
        return
    except Exception as e:
        await event.respond(f"❌ **Grup bulunamadı** veya hata: {e}")
        return

    ban_active = True
    baslangic_zamani = time.time()
    toplam_ban = 0
    ban_sayaci_lock = asyncio.Lock()

    await event.respond(f"🔥 **{BOT_NAME} 30000+ DELİ DEHŞET TARAMA MODU AKTİF!**\nGrup: **{chat.title}**\n**Kuralsız manyak kapasite** ile tarıyorum...")

    # === 30000+ ÜYE KAPASİTELİ FELAKET KURALSIZ TARAMA ===
    members = []
    try:
        offset = 0
        limit_per_request = 200  # Telegram'ın güvenli chunk boyutu
        max_attempts = 30000     # 30k+ kapasite zorlaması
        
        while len(members) < max_attempts:
            participants = await client(GetParticipantsRequest(
                channel=chat,
                filter=ChannelParticipantsSearch(''),
                offset=offset,
                limit=limit_per_request,
                hash=0
            ))
            
            if not participants.users:
                break
                
            for p in participants.users:
                if not getattr(p, 'bot', False) and not getattr(p, 'is_self', False):
                    members.append(p.id)
            
            offset += len(participants.users)
            
            # Her 5000 üyede bir ilerleme göster (çok büyük gruplarda takılmasın)
            if len(members) % 5000 == 0 and len(members) > 0:
                await event.respond(f"🔄 **Tarama devam...** Şu ana kadar çekilen: **{len(members)}** üye")
            
            await asyncio.sleep(0.05)  # Çok hafif delay, flood'u biraz yumuşat ama hızı koru
        
        total_members = len(members)
        if limit is None or limit > total_members:
            limit = total_members
        
        await event.respond(f"🚀 **30000+ DEHŞET TARAMA BİTTİ!**\nToplam normal üye: **{total_members}**\nBanlanacak: **{limit}** üye\n**{BOT_NAME} şimdi full gaz banlıyor...** 🔥🔥🔥")
    except Exception as e:
        await event.respond(f"⚠ **Tarama hatası:** {e}\nYine de elimdekiyle devam ediyorum...")
        members = []
        limit = 0

    # Kuyruk
    queue = asyncio.Queue(maxsize=CONCURRENT_BANS * 2)

    # İşçi (ban kısmı hiç değişmedi)
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

    # İşçileri başlat
    workers = [asyncio.create_task(ban_worker(i)) for i in range(CONCURRENT_BANS)]

    # Taranan üyeleri kuyruğa at (sadece limit kadar)
    for user_id in members[:limit]:
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
        f"Süre: **{gecen_sure:.1f}** saniye\n"
        f"**30000+ kapasite kuralsız tarama** aktifti 🔥"
    )

    ban_active = False


async def main():
    await client.start(bot_token=BOT_TOKEN)
    print("🚀 Bot çalışıyor...")
    await client.run_until_disconnected()

asyncio.run(main())
