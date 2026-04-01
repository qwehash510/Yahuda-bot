import os
import requests
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import GetParticipantRequest

# ---------------- AYARLAR ----------------
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN"))

# Grup kontrolü
ALLOWED_GROUP = "vxtikan"  # Grup kullanıcı adı
OWNER_IDS = [8620961678]  # Buraya bot sahibinin Telegram ID'si (int) ekle

# ---------------- TELETHON CLIENT ----------------
client = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# ---------------- YARDIMCI FONKSİYONLAR ----------------
def is_tiktok(url):
    return "tiktok.com" in url

def download_tiktok(url):
    """TikTok videolarını ve müziklerini indirir"""
    try:
        api = f"https://tikwm.com/api/?url={url}"
        r = requests.get(api).json()
        if r["code"] != 0:
            return None, None
        return r["data"]["play"], r["data"]["music"]
    except:
        return None, None

async def check_membership(user_id):
    """Kullanıcının gruba üye olup olmadığını kontrol eder"""
    if user_id in OWNER_IDS:
        return True  # Sahip her zaman onaylı
    try:
        await client(GetParticipantRequest(channel=ALLOWED_GROUP, user_id=user_id))
        return True
    except Exception as e:
        if "User not participant" in str(e):
            return False
        print(f"⚠️ Beklenmedik hata: {e}")
        return False

# ---------------- /START MENÜSÜ ----------------
@client.on(events.NewMessage(pattern="/start"))
async def start(event):
    if event.out:
        return

    user_id = event.sender_id
    if await check_membership(user_id):
        await event.reply(
            "🎉 Botu kullanmaya başlayabilirsiniz!\n\n"
            "📌 Kullanım:\n"
            "1️⃣ TikTok linkini kopyala\n"
            "2️⃣ Bana gönder\n"
            "3️⃣ Filigransız video ve MP3 sesini al\n\n"
            "🛠 Developer: @primalamazsin"
        )
        return

    # Kullanıcı üye değilse normal başlangıç menüsü
    await event.reply(
        "👋 Bu botu kullanabilmek için öncelikle grubumuza katılmalısınız.\n\n"
        f"🔹 Grup: t.me/{ALLOWED_GROUP}\n\n"
        "✅ Katıldıysanız aşağıdaki butona basarak doğrulayabilirsiniz.",
        buttons=[
            [Button.url("Gruba Katıl", f"https://t.me/{ALLOWED_GROUP}")],
            [Button.inline("Katıldım ✅", data="check_join")]
        ]
    )

# ---------------- ONAY BUTONU ----------------
@client.on(events.CallbackQuery(data="check_join"))
async def check_join(event):
    user_id = event.sender_id
    if await check_membership(user_id):
        await event.edit(
            "🎉 Onaylandı! Artık botu kullanabilirsiniz.\n\n"
            "📌 Kullanım:\n"
            "1️⃣ TikTok linkini kopyala\n"
            "2️⃣ Bana gönder\n"
            "3️⃣ Filigransız video ve MP3 sesini al\n\n"
            "🛠 Developer: @primalamazsin"
        )
    else:
        await event.answer("❌ Önce gruba katılmalısınız!", alert=True)

# ---------------- TIKTOK MESAJLARI ----------------
@client.on(events.NewMessage)
async def handler(event):
    if event.out:
        return

    user_id = event.sender_id
    if not await check_membership(user_id):
        return  # Üye değilse hiçbir şey yapma

    text = event.raw_text
    if is_tiktok(text):
        msg = await event.reply("⏳ TikTok indiriliyor, lütfen bekleyin...")
        video, music = download_tiktok(text)
        if not video:
            await msg.edit("❌ Video indirilemedi, linki kontrol edin!")
            return
        await msg.edit("✅ Video ve ses hazır, gönderiliyor...")
        await client.send_file(event.chat_id, video, caption="🎥 TikTok Video")
        await client.send_file(event.chat_id, music, caption="🎧 TikTok MP3")
        await msg.delete()
    else:
        if not text.startswith("/start"):
            await event.reply("📎 Lütfen geçerli bir TikTok linki gönderin!")

# ---------------- RUN ----------------
print("🤖 Bot çalışıyor...")
client.run_until_disconnected()
