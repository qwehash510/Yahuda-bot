import os
import time
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# SADECE SENİN ID
OWNER_ID = 123456789  # BURAYA KENDİ TELEGRAM ID YAZ

logging.basicConfig(
    format="%(asctime)s - YAHUDA - %(levelname)s - %(message)s",
    level=logging.INFO
)

guard_active = {}
user_messages = {}
join_times = {}

# OWNER kontrol
def is_owner(user_id):
    return user_id == OWNER_ID


# Guard aç / kapat
async def yahuda(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not is_owner(user_id):
        return

    if chat_id not in guard_active:

        guard_active[chat_id] = True

        await update.message.reply_text(
            "𐱅 YAHUDA GUARD AKTİF\n"
            "⚡ MAXIMUM PROTECTION ENABLED\n"
            "🛡 Sistem seni koruyor efendim."
        )

    else:

        guard_active.pop(chat_id)

        await update.message.reply_text(
            "𐱅 YAHUDA GUARD KAPATILDI"
        )


# Yeni kullanıcı koruma
async def new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    if chat_id not in guard_active:
        return

    now = time.time()

    for user in update.message.new_chat_members:

        # Fake hesap koruma (hesap çok yeni ise)
        if (now - user.id) < 86400:

            await context.bot.ban_chat_member(chat_id, user.id)

            await update.message.reply_text(
                f"𐱅 YAHUDA\n"
                f"Fake hesap yok edildi."
            )

            return

        # Raid koruma
        if chat_id not in join_times:
            join_times[chat_id] = []

        join_times[chat_id].append(now)

        join_times[chat_id] = [
            t for t in join_times[chat_id]
            if now - t < 10
        ]

        if len(join_times[chat_id]) > 5:

            await context.bot.ban_chat_member(chat_id, user.id)

            await update.message.reply_text(
                "𐱅 YAHUDA\n"
                "Raid tespit edildi.\n"
                "Tehdit yok edildi."
            )


# Mesaj koruma
async def message_control(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    if chat_id not in guard_active:
        return

    user_id = update.effective_user.id
    text = update.message.text.lower()
    now = time.time()

    # Link koruma
    if "http" in text or "t.me" in text:

        await update.message.delete()

        return

    # Spam koruma
    if user_id not in user_messages:
        user_messages[user_id] = []

    user_messages[user_id].append(now)

    user_messages[user_id] = [
        t for t in user_messages[user_id]
        if now - t < 5
    ]

    if len(user_messages[user_id]) > 6:

        await context.bot.ban_chat_member(chat_id, user_id)

        await context.bot.send_message(
            chat_id,
            "𐱅 YAHUDA\nSpam yapan yok edildi."
        )


# Bot başlat
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

    print("YAHUDA OWNER GUARD AKTİF")

    app.run_polling()


if __name__ == "__main__":
    main()
