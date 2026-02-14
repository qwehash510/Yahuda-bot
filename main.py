import logging
from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = "8317082439:AAE5vuI6Agf6EjqEUSsg5_LK2hSZ--GxZlI"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ROLLER
ROLES = {
    "kurucu": [],
    "yardimci_kurucu": [],
    "admin": [],
    "moderator": [],
    "susturucu": []
}

# HOŞ GELDİN MESAJI
WELCOME_MSG = """
𖤐 YAHUDA #KABİLE 𖤐

Hoş geldin {name}

Bu kabile güç, sadakat ve kontrolden oluşur.
Kurallara uy, saygı göster, gücünü kanıtla.

Yetkililer her zaman izliyor.
"""

# ROL KONTROL
def has_role(user_id, role):
    return user_id in ROLES[role]

def is_staff(user_id):
    for role in ROLES:
        if user_id in ROLES[role]:
            return True
    return False

# BAŞLAT
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "𖤐 YAHUDA BOT AKTİF\n\nKomutlar:\n"
        "/yetkiver id rol\n"
        "/yetkial id rol\n"
        "/ban id\n"
        "/kick id\n"
        "/mute id\n"
        "/unmute id\n"
        "/temizle sayı"
    )

# HOŞ GELDİN
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        await update.message.reply_text(
            WELCOME_MSG.format(name=user.first_name)
        )

# YETKİ VER
async def yetkiver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.id

    if not has_role(sender, "kurucu"):
        return

    try:
        user_id = int(context.args[0])
        role = context.args[1]

        if role in ROLES:
            ROLES[role].append(user_id)
            await update.message.reply_text("Yetki verildi.")
        else:
            await update.message.reply_text("Rol bulunamadı.")

    except:
        await update.message.reply_text("Kullanım: /yetkiver id rol")

# YETKİ AL
async def yetkial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.id

    if not has_role(sender, "kurucu"):
        return

    try:
        user_id = int(context.args[0])
        role = context.args[1]

        if role in ROLES and user_id in ROLES[role]:
            ROLES[role].remove(user_id)
            await update.message.reply_text("Yetki alındı.")

    except:
        pass

# BAN
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.id

    if not is_staff(sender):
        return

    try:
        user_id = int(context.args[0])
        await context.bot.ban_chat_member(update.effective_chat.id, user_id)
        await update.message.reply_text("Kullanıcı banlandı.")
    except:
        pass

# KICK
async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.id

    if not is_staff(sender):
        return

    try:
        user_id = int(context.args[0])
        await context.bot.ban_chat_member(update.effective_chat.id, user_id)
        await context.bot.unban_chat_member(update.effective_chat.id, user_id)
        await update.message.reply_text("Kullanıcı atıldı.")
    except:
        pass

# MUTE
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.id

    if not is_staff(sender):
        return

    try:
        user_id = int(context.args[0])

        permissions = ChatPermissions(
            can_send_messages=False
        )

        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            user_id,
            permissions
        )

        await update.message.reply_text("Susturuldu.")

    except:
        pass

# UNMUTE
async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.id

    if not is_staff(sender):
        return

    try:
        user_id = int(context.args[0])

        permissions = ChatPermissions(
            can_send_messages=True
        )

        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            user_id,
            permissions
        )

        await update.message.reply_text("Susturma kaldırıldı.")

    except:
        pass

# TEMİZLE
async def temizle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.id

    if not is_staff(sender):
        return

    try:
        count = int(context.args[0])

        for i in range(count):
            await context.bot.delete_message(
                update.effective_chat.id,
                update.message.message_id - i
            )

    except:
        pass


# BOT BAŞLAT
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("yetkiver", yetkiver))
app.add_handler(CommandHandler("yetkial", yetkial))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("kick", kick))
app.add_handler(CommandHandler("mute", mute))
app.add_handler(CommandHandler("unmute", unmute))
app.add_handler(CommandHandler("temizle", temizle))
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))

print("YAHUDA BOT AKTİF")

app.run_polling()
