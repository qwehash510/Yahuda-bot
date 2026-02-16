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

TOKEN = os.getenv("BOT_TOKEN")

# SAHİP USERNAME
OWNER = "kullanici_adin"

# GUARD DURUM
YAHUDA_CORE = False

# VERİLER
WHITELIST = set([OWNER])
SPAM = {}
RAID = {}

# AYARLAR
SPAM_LIMIT = 5
SPAM_TIME = 8

RAID_LIMIT = 4
RAID_TIME = 10

LINK = r"(https?://|t.me|telegram.me)"

# LOG
logging.basicConfig(
    level=logging.INFO,
    format="YAHUDA CORE >> %(message)s"
)


# YAHUDA BAŞLAT
async def guard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global YAHUDA_CORE

    user = update.effective_user.username

    if user != OWNER:
        return

    YAHUDA_CORE = not YAHUDA_CORE

    if YAHUDA_CORE:

        await update.message.reply_text(
            "𖤐 YAHUDA CORE AKTİF\n"
            "Sistem koruması başlatıldı.\n\n"
            "Anti-Raid: AKTİF\n"
            "Anti-Link: AKTİF\n"
            "Anti-Spam: AKTİF\n"
            "Admin Shield: AKTİF"
        )

    else:

        await update.message.reply_text(
            "𖤐 YAHUDA CORE DEVRE DIŞI"
        )


# ANA KORUMA
async def yahuda_guard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not YAHUDA_CORE:
        return

    user = update.effective_user
    chat = update.effective_chat
    msg = update.message

    if not user.username:
        return

    if user.username in WHITELIST:
        return

    text = msg.text.lower()

    # LINK TESPİT
    if re.search(LINK, text):

        await msg.delete()

        await chat.ban_member(user.id)

        await chat.send_message(
            f"𖤐 YAHUDA FIREWALL\n"
            f"Tehdit yok edildi.\n"
            f"Kullanıcı: @{user.username}\n"
            f"Sebep: Yetkisiz link"
        )

        return

    # SPAM TESPİT
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
            f"𖤐 YAHUDA DEFENSE\n"
            f"Spam saldırısı engellendi.\n"
            f"Kullanıcı: @{user.username}"
        )


# RAID KORUMA
async def yahuda_join(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not YAHUDA_CORE:
        return

    chat = update.effective_chat

    for user in update.message.new_chat_members:

        if user.is_bot:

            await chat.ban_member(user.id)

            await chat.send_message(
                "𖤐 YAHUDA SHIELD\n"
                "Yetkisiz bot imha edildi."
            )

            return

        now = time.time()

        if chat.id not in RAID:
            RAID[chat.id] = []

        RAID[chat.id].append(now)

        RAID[chat.id] = [
            t for t in RAID[chat.id]
            if now - t < RAID_TIME
        ]

        if len(RAID[chat.id]) >= RAID_LIMIT:

            await chat.ban_member(user.id)

            await chat.send_message(
                "𖤐 YAHUDA CORE\n"
                "Raid saldırısı durduruldu."
            )


# ADMIN KORUMA
async def yahuda_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not YAHUDA_CORE:
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
            f"𖤐 YAHUDA SECURITY\n"
            f"Yetkisiz admin silindi.\n"
            f"Hedef: @{user.username}"
        )


# MAIN
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("guard", guard))

    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        yahuda_guard
    ))

    app.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS,
        yahuda_join
    ))

    app.add_handler(ChatMemberHandler(
        yahuda_admin,
        ChatMemberHandler.CHAT_MEMBER
    ))

    print("YAHUDA CORE ONLINE")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
