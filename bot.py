import os
import logging
import asyncio
from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - YAHUDA - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Guard durumu
guard_groups = {}

# Spam sistemi
user_messages = {}

# Küfür listesi
bad_words = ["oç", "amk", "piç", "sik", "orospu"]

# Link filtresi
link_filter = True


# YAHUDA aç / kapat
async def yahuda(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat.type == "private":
        await update.message.reply_text("Bu komut sadece gruplarda çalışır.")
        return

    chat_id = update.effective_chat.id

    if chat_id not in guard_groups:
        guard_groups[chat_id] = True
        await update.message.reply_text(
            "𐱅 YAHUDA GUARD AKTİF\n"
            "⚡ Sistem çevrimiçi\n"
            "🛡 Koruma başlatıldı"
        )
    else:
        guard_groups.pop(chat_id)
        await update.message.reply_text(
            "𐱅 YAHUDA GUARD KAPATILDI\n"
            "⚠ Sistem devre dışı"
        )


# Yeni kullanıcı
async def new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    if chat_id not in guard_groups:
        return

    for user in update.message.new_chat_members:

        await update.message.reply_text(
            f"𐱅 Hoş geldin {user.first_name}\n"
            "YAHUDA seni izliyor..."
        )


# Mesaj kontrol
async def message_control(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    if chat_id not in guard_groups:
        return

    user_id = update.effective_user.id
    text = update.message.text.lower()

    # Link koruma
    if "http" in text or "t.me" in text:

        await update.message.delete()

        await update.message.reply_text(
            "𐱅 YAHUDA\n"
            "Link engellendi."
        )

        return

    # Küfür koruma
    for word in bad_words:

        if word in text:

            await update.message.delete()

            await update.message.reply_text(
                "𐱅 YAHUDA\n"
                "Küfür engellendi."
            )

            return

    # Spam koruma
    now = asyncio.get_event_loop().time()

    if user_id not in user_messages:
        user_messages[user_id] = []

    user_messages[user_id].append(now)

    user_messages[user_id] = [
        t for t in user_messages[user_id]
        if now - t < 5
    ]

    if len(user_messages[user_id]) > 5:

        await context.bot.ban_chat_member(
            chat_id,
            user_id
        )

        await update.message.reply_text(
            "𐱅 YAHUDA\n"
            "Spam tespit edildi.\n"
            "Kullanıcı yok edildi."
        )


# Başlat
def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("yahuda", yahuda))

    app.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS,
        new_user
    ))

    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        message_control
    ))

    print("YAHUDA AKTİF")

    app.run_polling()


if __name__ == "__main__":
    main()
