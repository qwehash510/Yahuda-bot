import os
import logging
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ChatMemberHandler

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# yardımcı kurucu listesi
sudo_users = set()

# spam kontrol
message_count = {}

# hoş geldin
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.new_chat_members:
        for user in update.message.new_chat_members:
            await update.message.reply_text(
                f"""
☠️ YAHUDA #KABİLE SİSTEMİ ☠️

⚡ {user.mention_html()} sisteme giriş yaptı.

🛡 Bu kabile korunmaktadır.
🔥 Tüm hareketler izleniyor.

Hoş geldin.
""",
                parse_mode="HTML"
            )

# hoşçakal
async def goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.left_chat_member:
        user = update.message.left_chat_member
        await update.message.reply_text(
            f"""
☠️ YAHUDA #KABİLE ☠️

⚡ {user.full_name} sistemden ayrıldı.

🕶 İzler silindi.
"""
        )

# yardımcı kurucu ekle
async def addsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    admins = await update.effective_chat.get_administrators()

    if user.id not in [admin.user.id for admin in admins]:
        return

    if context.args:
        sudo_users.add(int(context.args[0]))
        await update.message.reply_text("Yardımcı kurucu eklendi.")

# ban
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    admins = await update.effective_chat.get_administrators()

    if user.id not in [admin.user.id for admin in admins] and user.id not in sudo_users:
        return

    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user.id
        await context.bot.ban_chat_member(update.effective_chat.id, target)
        await update.message.reply_text("Kullanıcı banlandı.")

# kick
async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    admins = await update.effective_chat.get_administrators()

    if user.id not in [admin.user.id for admin in admins] and user.id not in sudo_users:
        return

    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user.id
        await context.bot.unban_chat_member(update.effective_chat.id, target)
        await update.message.reply_text("Kullanıcı atıldı.")

# sustur
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    admins = await update.effective_chat.get_administrators()

    if user.id not in [admin.user.id for admin in admins] and user.id not in sudo_users:
        return

    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user.id

        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            target,
            ChatPermissions(can_send_messages=False)
        )

        await update.message.reply_text("Kullanıcı susturuldu.")

# susturma kaldır
async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    admins = await update.effective_chat.get_administrators()

    if user.id not in [admin.user.id for admin in admins] and user.id not in sudo_users:
        return

    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user.id

        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            target,
            ChatPermissions(can_send_messages=True)
        )

        await update.message.reply_text("Kullanıcının susturması kaldırıldı.")

# link koruma
async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.lower()

    if "http" in text or "t.me" in text:

        user = update.effective_user

        admins = await update.effective_chat.get_administrators()

        if user.id in [admin.user.id for admin in admins] or user.id in sudo_users:
            return

        await update.message.delete()

# spam koruma
async def anti_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in message_count:
        message_count[user_id] = 0

    message_count[user_id] += 1

    if message_count[user_id] > 7:
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            user_id,
            ChatPermissions(can_send_messages=False)
        )

# staff list
async def staff(update: Update, context: ContextTypes.DEFAULT_TYPE):

    admins = await update.effective_chat.get_administrators()

    text = "STAFF LİSTESİ:\n\n"

    for admin in admins:
        text += f"- {admin.user.full_name}\n"

    await update.message.reply_text(text)

# start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "YAHUDA #KABİLE BOT AKTİF"
    )


def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("staff", staff))
    app.add_handler(CommandHandler("addsudo", addsudo))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, anti_link))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, anti_spam))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, goodbye))

    print("BOT AKTİF")

    app.run_polling()


if __name__ == "__main__":
    main()
