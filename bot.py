import os
import logging
from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

# =========================
# YETKİ SİSTEMİ
# =========================

kurucu = None
yardimci_kurucu = set()
adminler = set()
modlar = set()
stafflar = set()

# =========================
# KORUMA
# =========================

full_koruma = False


# =========================
# KONTROL
# =========================

def is_kurucu(user):
    return user.username == kurucu

def is_yk(user):
    return user.username in yardimci_kurucu or is_kurucu(user)

def is_admin(user):
    return user.username in adminler or is_yk(user)

def is_mod(user):
    return user.username in modlar or is_admin(user)

def is_staff(user):
    return user.username in stafflar or is_mod(user)


# =========================
# BAŞLAT
# =========================

async def santana(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global kurucu

    user = update.effective_user

    if kurucu is None:
        kurucu = user.username

        await update.message.reply_text(
            f"""
👑 YAHUDA #KRALLIK AKTİF

Kurucu: @{user.username}

Bot hazır.
"""
        )
    else:
        await update.message.reply_text("Bot zaten aktif.")


# =========================
# YARDIMCI KURUCU VER / AL
# =========================

async def ykurucu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_kurucu(update.effective_user):
        return

    username = context.args[0].replace("@","")

    yardimci_kurucu.add(username)

    await update.message.reply_text(f"⚡ @{username} yardımcı kurucu yapıldı")


async def ykurucual(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_kurucu(update.effective_user):
        return

    username = context.args[0].replace("@","")

    yardimci_kurucu.discard(username)

    await update.message.reply_text(f"❌ @{username} yardımcı kurucu alındı")


# =========================
# ADMIN VER / AL
# =========================

async def adminver(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_yk(update.effective_user):
        return

    username = context.args[0].replace("@","")

    adminler.add(username)

    await update.message.reply_text(f"🛡 @{username} admin yapıldı")


async def adminal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_yk(update.effective_user):
        return

    username = context.args[0].replace("@","")

    adminler.discard(username)

    await update.message.reply_text(f"❌ @{username} admin alındı")


# =========================
# MOD VER / AL
# =========================

async def modver(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user):
        return

    username = context.args[0].replace("@","")

    modlar.add(username)

    await update.message.reply_text(f"⚔ @{username} mod yapıldı")


async def modal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user):
        return

    username = context.args[0].replace("@","")

    modlar.discard(username)

    await update.message.reply_text(f"❌ @{username} mod alındı")


# =========================
# STAFF VER / AL
# =========================

async def staffver(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_mod(update.effective_user):
        return

    username = context.args[0].replace("@","")

    stafflar.add(username)

    await update.message.reply_text(f"⚡ @{username} staff yapıldı")


async def staffal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_mod(update.effective_user):
        return

    username = context.args[0].replace("@","")

    stafflar.discard(username)

    await update.message.reply_text(f"❌ @{username} staff alındı")


# =========================
# STAFF PANEL
# =========================

async def staffpanel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = "👑 YAHUDA #KRALLIK STAFF\n\n"

    text += f"Kurucu: @{kurucu}\n\n"

    text += "Yardımcı Kurucu:\n"
    for u in yardimci_kurucu:
        text += f"@{u}\n"

    text += "\nAdmin:\n"
    for u in adminler:
        text += f"@{u}\n"

    text += "\nMod:\n"
    for u in modlar:
        text += f"@{u}\n"

    text += "\nStaff:\n"
    for u in stafflar:
        text += f"@{u}\n"

    await update.message.reply_text(text)


# =========================
# BAN / UNBAN
# =========================

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_mod(update.effective_user):
        return

    user = context.args[0]

    member = await context.bot.get_chat_member(
        update.effective_chat.id,
        user
    )

    await context.bot.ban_chat_member(
        update.effective_chat.id,
        member.user.id
    )

    await update.message.reply_text(f"⛔ {user} banlandı")


async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_mod(update.effective_user):
        return

    user = context.args[0]

    member = await context.bot.get_chat_member(
        update.effective_chat.id,
        user
    )

    await context.bot.unban_chat_member(
        update.effective_chat.id,
        member.user.id
    )

    await update.message.reply_text(f"✅ {user} unbanlandı")


# =========================
# MUTE / UNMUTE
# =========================

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_mod(update.effective_user):
        return

    user = context.args[0]

    member = await context.bot.get_chat_member(
        update.effective_chat.id,
        user
    )

    await context.bot.restrict_chat_member(
        update.effective_chat.id,
        member.user.id,
        ChatPermissions(can_send_messages=False)
    )

    await update.message.reply_text(f"🔇 {user} mute edildi")


async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_mod(update.effective_user):
        return

    user = context.args[0]

    member = await context.bot.get_chat_member(
        update.effective_chat.id,
        user
    )

    await context.bot.restrict_chat_member(
        update.effective_chat.id,
        member.user.id,
        ChatPermissions(can_send_messages=True)
    )

    await update.message.reply_text(f"🔊 {user} unmute edildi")


# =========================
# TEMİZLE
# =========================

async def temizle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_mod(update.effective_user):
        return

    sayı = int(context.args[0])

    await update.message.reply_text(f"🧹 {sayı} mesaj temizlendi")


# =========================
# FULL KORUMA
# =========================

async def fullkoruma(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global full_koruma

    if not is_admin(update.effective_user):
        return

    full_koruma = True

    await update.message.reply_text("🛡 FULL KORUMA AKTİF")


# =========================
# SPAM KORUMA
# =========================

async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if full_koruma:

        if "http" in update.message.text.lower():

            if not is_staff(update.effective_user):

                await update.message.delete()


# =========================
# MAIN
# =========================

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("santana", santana))

    app.add_handler(CommandHandler("ykurucu", ykurucu))
    app.add_handler(CommandHandler("ykurucual", ykurucual))

    app.add_handler(CommandHandler("adminver", adminver))
    app.add_handler(CommandHandler("adminal", adminal))

    app.add_handler(CommandHandler("modver", modver))
    app.add_handler(CommandHandler("modal", modal))

    app.add_handler(CommandHandler("staffver", staffver))
    app.add_handler(CommandHandler("staffal", staffal))

    app.add_handler(CommandHandler("staffpanel", staffpanel))

    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))

    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))

    app.add_handler(CommandHandler("temizle", temizle))

    app.add_handler(CommandHandler("fullkoruma", fullkoruma))

    app.add_handler(MessageHandler(filters.TEXT, mesaj))

    print("YAHUDA KRALLIK AKTİF")

    app.run_polling()


if __name__ == "__main__":
    main()
