import os
import logging
import time
import re
import asyncio

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ChatMemberHandler,
    filters
)

# TOKEN Railway environment variable
TOKEN = os.getenv("BOT_TOKEN")

# OWNER username (değiştir)
OWNER = "kullanici_adin"

# GUARD DURUM
GUARD = False

# VERİLER
WHITELIST = set([OWNER])
SPAM = {}
JOINS = {}

# AYARLAR
SPAM_LIMIT = 6
SPAM_TIME = 10
RAID_LIMIT = 5
RAID_TIME = 10

LINK_REGEX = r"(https?://|t.me|telegram.me)"
BAD_WORDS = ["amk", "aq", "orospu", "piç"]

# LOG
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)


# GUARD KOMUTU (TEK KOMUT)
async def guard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global GUARD

    user = update.effective_user.username

    if user != OWNER:
        return

    GUARD = not GUARD

    if GUARD:
        await update.message.reply_text("🛡 Guard aktif")
    else:
        await update.message.reply_text("❌ Guard kapalı")


# ANA KORUMA
async def message_guard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not GUARD:
        return

    user = update.effective_user
    chat = update.effective_chat
    message = update.message

    if not user.username:
        return

    if user.username in WHITELIST:
        return

    text = message.text.lower()

    # LINK KORUMA
    if re.search(LINK_REGEX, text):

        await message.delete()
        await chat.ban_member(user.id)

        await chat.send_message(
            f"🚫 Link atan banlandı\n@{user.username}"
        )

        return

    # KÜFÜR KORUMA
    for word in BAD_WORDS:

        if word in text:

            await message.delete()

            await chat.send_message(
                f"⚠ Küfür yasak\n@{user.username}"
            )

            return

    # SPAM KORUMA
    now = time.time()

    if user.id not in SPAM:
        SPAM[user.id] = []

    SPAM[user.id].append(now)

    SPAM[user.id] = [
        t for t in SPAM[user.id]
        if now - t < SPAM_TIME
    ]

    if len(SPAM[user.id]) >= SPAM_LIMIT:

        await chat.ban_member(user.id)

        await chat.send_message(
            f"🚫 Spam nedeniyle ban\n@{user.username}"
        )


# BOT + RAID KORUMA
async def join_guard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not GUARD:
        return

    chat = update.effective_chat

    for user in update.message.new_chat_members:

        # BOT KORUMA
        if user.is_bot:

            await chat.ban_member(user.id)

            await chat.send_message(
                f"🤖 Bot engellendi"
            )

            return

        # RAID KORUMA
        now = time.time()

        if chat.id not in JOINS:
            JOINS[chat.id] = []

        JOINS[chat.id].append(now)

        JOINS[chat.id] = [
            t for t in JOINS[chat.id]
            if now - t < RAID_TIME
        ]

        if len(JOINS[chat.id]) >= RAID_LIMIT:

            await chat.ban_member(user.id)

            await chat.send_message(
                f"⚠ Raid engellendi"
            )


# ADMIN KORUMA
async def admin_guard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not GUARD:
        return

    user = update.chat_member.new_chat_member.user

    if not user.username:
        return

    if user.username in WHITELIST:
        return

    if update.chat_member.new_chat_member.status == "administrator":

        await context.bot.ban_chat_member(
            update.effective_chat.id,
            user.id
        )

        await context.bot.send_message(
            update.effective_chat.id,
            f"🚫 Yetkisiz admin banlandı\n@{user.username}"
        )


# MAIN
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("guard", guard))

    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        message_guard
    ))

    app.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS,
        join_guard
    ))

    app.add_handler(ChatMemberHandler(
        admin_guard,
        ChatMemberHandler.CHAT_MEMBER
    ))

    print("MAX GUARD AKTİF")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
