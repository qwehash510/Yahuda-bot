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

# =========================
# AYARLAR
# =========================

TOKEN = os.getenv("BOT_TOKEN")

# BURAYA KENDİ TELEGRAM ID'ni YAZDIN
OWNER_ID = 8464933639

SP_LEVEL = 20

koruma_aktif = True
raid_koruma = True
admin_bildirim = True

raid_log = {}
raid_limit = 5
raid_time = 10

mesajlar = {
    "raid": "⚠️ TEHDİT ALGILANDI\n🛡️ SP20 ULTRA GUARD saldırıyı engelledi.",
    "admin": "🚨 ADMIN EKLENDİ"
}

logging.basicConfig(level=logging.INFO)

# =========================
# SADECE OWNER KOMUT KULLANABİLİR
# =========================

def owner_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != OWNER_ID:
            return
        return await func(update, context)
    return wrapper

# =========================
# PANEL
# =========================

@owner_only
async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""
🛡️ SP20 ULTRA GUARD PANEL

Koruma: {'Aktif' if koruma_aktif else 'Kapalı'}
Raid Koruma: {'Aktif' if raid_koruma else 'Kapalı'}
Admin Bildirim: {'Aktif' if admin_bildirim else 'Kapalı'}

Seviye: SP{SP_LEVEL}
"""
    await update.message.reply_text(text)

# =========================
# RAID ALGILAMA
# =========================

async def yeni_kullanici(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not raid_koruma:
        return

    chat_id = update.effective_chat.id

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

        await context.bot.set_chat_permissions(
            chat_id,
            ChatPermissions(
                can_send_messages=False
            )
        )

# =========================
# ADMIN EKLENME BİLDİRİMİ
# =========================

async def admin_kontrol(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not admin_bildirim:
        return

    member = update.chat_member

    if member.new_chat_member.status in ["administrator"]:

        user = member.new_chat_member.user

        await context.bot.send_message(
            OWNER_ID,
            f"""
🚨 YENİ ADMIN EKLENDİ

👤 {user.full_name}
🆔 {user.id}
📍 Grup: {update.effective_chat.title}
"""
        )

# =========================
# KORUMA KOMUTLARI
# =========================

@owner_only
async def koruma_ac(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global koruma_aktif
    koruma_aktif = True
    await update.message.reply_text("✅ Koruma aktif edildi")

@owner_only
async def koruma_kapat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global koruma_aktif
    koruma_aktif = False
    await update.message.reply_text("❌ Koruma kapatıldı")

# =========================
# ANA
# =========================

async def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CommandHandler("koruma_ac", koruma_ac))
    app.add_handler(CommandHandler("koruma_kapat", koruma_kapat))

    app.add_handler(ChatMemberHandler(admin_kontrol, ChatMemberHandler.CHAT_MEMBER))

    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            yeni_kullanici
        )
    )

    print("SP20 ULTRA GUARD AKTİF")

    await app.run_polling()

# =========================

if __name__ == "__main__":
    asyncio.run(main())
