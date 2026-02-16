import os
import time
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Railway Variables
TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

# logging
logging.basicConfig(
    format="%(asctime)s - YAHUDA ABYSS - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Sistem
GUARD = False
WHITELIST = set()
SPAM = {}
RAID = []

# Owner ekle
WHITELIST.add(OWNER_ID)


# Owner kontrol
def is_owner(user_id):
    return user_id == OWNER_ID


# whitelist kontrol
def is_whitelist(user_id):
    return user_id in WHITELIST


# Guard aç/kapat
async def yahuda(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global GUARD

    if not is_owner(update.effective_user.id):
        return

    if not GUARD:

        GUARD = True

        await update.message.reply_text(
            "𐱅 YAHUDA ABYSS CORE AKTİF\n"
            "⚡ Dark system online\n"
            "👁‍🗨 Threat monitor enabled\n"
            "🛡 Maximum protection"
        )

    else:

        GUARD = False

        await update.message.reply_text(
            "𐱅 YAHUDA CORE DEVRE DIŞI"
        )


# whitelist ekle
async def allow(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_owner(update.effective_user.id):
        return

    try:

        user_id = int(context.args[0])

        WHITELIST.add(user_id)

        await update.message.reply_text(
            "Kullanıcı beyaz listeye eklendi"
        )

    except:

        await update.message.reply_text(
            "Kullanım: /allow ID"
        )


# whitelist kaldır
async def deny(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_owner(update.effective_user.id):
        return

    try:

        user_id = int(context.args[0])

        WHITELIST.remove(user_id)

        await update.message.reply_text(
            "Whitelist kaldırıldı"
        )

    except:

        await update.message.reply_text(
            "Kullanım: /deny ID"
        )


# Raid koruma
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global RAID

    if not GUARD:
        return

    now = time.time()

    for user in update.message.new_chat_members:

        if is_whitelist(user.id):
            return

        RAID.append(now)

        RAID = [t for t in RAID if now - t < 10]

        if len(RAID) > 7:

            await context.bot.ban_chat_member(
                update.effective_chat.id,
                user.id
            )

            await context.bot.send_message(
                update.effective_chat.id,
                "☠ YAHUDA\nRaid detected\nTarget eliminated"
            )


# Spam ve link koruma
async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not GUARD:
        return

    user_id = update.effective_user.id

    if is_whitelist(user_id):
        return

    text = update.message.text.lower()
    now = time.time()

    # link koruma
    if "http" in text or "t.me" in text:

        await update.message.delete()
        return

    # spam koruma
    if user_id not in SPAM:
        SPAM[user_id] = []

    SPAM[user_id].append(now)

    SPAM[user_id] = [t for t in SPAM[user_id] if now - t < 5]

    if len(SPAM[user_id]) > 6:

        await context.bot.ban_chat_member(
            update.effective_chat.id,
            user_id
        )

        await context.bot.send_message(
            update.effective_chat.id,
            "☠ YAHUDA\nSpam detected\nUser destroyed"
        )


# başlat
def main():

    if not TOKEN:
        print("TOKEN YOK")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("yahuda", yahuda))
    app.add_handler(CommandHandler("allow", allow))
    app.add_handler(CommandHandler("deny", deny))

    app.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS,
        join
    ))

    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        message
    ))

    print("YAHUDA ABYSS CORE ONLINE")

    app.run_polling()


if __name__ == "__main__":
    main()
