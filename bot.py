import logging
import os
import asyncio
from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

# ==============================
# AYARLAR
# ==============================

TOKEN = "8317082439:AAHwANKyHEocB8cG-kV-9gM_7EgeJSQN4Pc"

OWNER_ID = 8464933639

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# ==============================
# OWNER KONTROL
# ==============================

def is_owner(user_id):
    return user_id == OWNER_ID

# ==============================
# KOMUTLAR
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if not is_owner(user.id):
        return

    await update.message.reply_text(
        "⚡ YAHUDA GUARD AKTİF\n"
        "🛡 Sistem Online\n"
        "👑 Owner kontrolü sağlandı"
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if not is_owner(user.id):
        return

    await update.message.reply_text(
        "⛔ YAHUDA GUARD DURDURULDU"
    )

    os._exit(0)


# ==============================
# RAID KORUMA
# ==============================

message_count = {}
TIME_LIMIT = 10
LIMIT = 6


async def message_control(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if user.id == OWNER_ID:
        return

    now = asyncio.get_event_loop().time()

    if user.id not in message_count:
        message_count[user.id] = []

    message_count[user.id].append(now)

    message_count[user.id] = [
        t for t in message_count[user.id]
        if now - t < TIME_LIMIT
    ]

    if len(message_count[user.id]) >= LIMIT:

        try:

            await context.bot.restrict_chat_member(
                chat_id=update.effective_chat.id,
                user_id=user.id,
                permissions=ChatPermissions(can_send_messages=False)
            )

            await update.effective_chat.send_message(
                f"🚨 TEHDİT ENGELLENDİ\n"
                f"Kullanıcı: {user.first_name}"
            )

        except:
            pass


# ==============================
# MAIN
# ==============================

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_control
        )
    )

    print("BOT AKTİF")

    app.run_polling()


if __name__ == "__main__":
    main()
