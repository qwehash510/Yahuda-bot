import os
import logging
import asyncio
from datetime import datetime, timedelta

from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    filters
)

# ==============================
# AYARLAR
# ==============================

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("8464933639"))

SP_LEVEL = 20

koruma_aktif = True
raid_koruma = True
admin_bildirim = True

raid_log = {}
raid_limit = 5
raid_time = 10

mesajlar = {
    "raid": "⚠️ TEHDİT ALGILANDI\n🛡️ SP20 ULTRA koruma saldırıyı engelledi",
    "admin": "🚨 ADMIN EKLENDİ",
}

logging.basicConfig(level=logging.INFO)

# ==============================
# YARDIMCI
# ==============================

def owner_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != OWNER_ID:
            return
        return await func(update, context)
    return wrapper

# ==============================
# KOMUTLAR
# ==============================

@owner_only
async def koruma_ac(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global koruma_aktif
    koruma_aktif = True
    await update.message.reply_text("🛡️ SP20 Ultra koruma AKTİF")

@owner_only
async def koruma_kapat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global koruma_aktif
    koruma_aktif = False
    await update.message.reply_text("❌ Koruma kapatıldı")

@owner_only
async def raid_koruma_ac(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global raid_koruma
    raid_koruma = True
    await update.message.reply_text("🚨 Raid koruma AKTİF")

@owner_only
async def raid_koruma_kapat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global raid_koruma
    raid_koruma = False
    await update.message.reply_text("❌ Raid koruma kapatıldı")

@owner_only
async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = f"""
🛡️ SP{SP_LEVEL} ULTRA PANEL

Koruma: {"AKTİF" if koruma_aktif else "KAPALI"}
Raid: {"AKTİF" if raid_koruma else "KAPALI"}
Admin Bildirim: {"AKTİF" if admin_bildirim else "KAPALI"}
    """

    await update.message.reply_text(text)

@owner_only
async def mesaj_ayarla(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        tip = context.args[0]
        yeni = " ".join(context.args[1:])
        mesajlar[tip] = yeni

        await update.message.reply_text("✅ Mesaj değiştirildi")

    except:
        await update.message.reply_text("Kullanım: /mesaj_ayarla raid mesaj")

# ==============================
# RAID KORUMA
# ==============================

async def mesaj_kontrol(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not koruma_aktif or not raid_koruma:
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    now = datetime.now()

    if chat_id not in raid_log:
        raid_log[chat_id] = []

    raid_log[chat_id].append(now)

    raid_log[chat_id] = [
        t for t in raid_log[chat_id]
        if now - t < timedelta(seconds=raid_time)
    ]

    if len(raid_log[chat_id]) >= raid_limit:

        await context.bot.send_message(
            chat_id,
            mesajlar["raid"]
        )

        raid_log[chat_id] = []

# ==============================
# ADMIN EKLENME KONTROL
# ==============================

async def admin_kontrol(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not koruma_aktif or not admin_bildirim:
        return

    result = update.chat_member

    if result.new_chat_member.status == "administrator":

        user = result.new_chat_member.user

        text = f"""
{mesajlar["admin"]}

👤 {user.full_name}
🆔 {user.id}
📍 {update.effective_chat.title}
        """

        await context.bot.send_message(
            OWNER_ID,
            text
        )

# ==============================
# BAŞLAT
# ==============================

async def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("koruma_ac", koruma_ac))
    app.add_handler(CommandHandler("koruma_kapat", koruma_kapat))
    app.add_handler(CommandHandler("raid_koruma_ac", raid_koruma_ac))
    app.add_handler(CommandHandler("raid_koruma_kapat", raid_koruma_kapat))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CommandHandler("mesaj_ayarla", mesaj_ayarla))

    app.add_handler(MessageHandler(filters.TEXT, mesaj_kontrol))
    app.add_handler(ChatMemberHandler(admin_kontrol))

    print(f"SP{SP_LEVEL} ULTRA BOT AKTİF")

    await app.run_polling()

# ==============================

if __name__ == "__main__":
    asyncio.run(main())
