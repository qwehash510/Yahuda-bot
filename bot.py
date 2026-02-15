import json
import logging
from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = "BOT_TOKEN_BURAYA"

logging.basicConfig(level=logging.INFO)

DATA_FILE = "data.json"

# Veri yükle
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "founders": [],
            "co_founders": [],
            "admins": [],
            "banned": [],
            "protection": False
        }

# Veri kaydet
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()


# Kurucu ekleme (ilk kullanan kurucu olur)
async def kurucu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    if len(data["founders"]) == 0:
        data["founders"].append(user)
        save_data(data)
        await update.message.reply_text("𖤐 YAHUDA #KABİLE\nKurucu olarak atandın.")
    else:
        await update.message.reply_text("Kurucu zaten var.")


# Yetki ver
async def yetki_ver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    if user not in data["founders"] and user not in data["co_founders"]:
        return await update.message.reply_text("Yetkin yok.")

    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user.id
        if target not in data["admins"]:
            data["admins"].append(target)
            save_data(data)
            await update.message.reply_text("Yetki verildi.")


# Yetki al
async def yetki_al(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    if user not in data["founders"] and user not in data["co_founders"]:
        return

    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user.id
        if target in data["admins"]:
            data["admins"].remove(target)
            save_data(data)
            await update.message.reply_text("Yetki alındı.")


# Staff list
async def staff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "𖤐 YAHUDA #KABİLE STAFF\n\n"

    text += "Kurucular:\n"
    for x in data["founders"]:
        text += f"• {x}\n"

    text += "\nAdminler:\n"
    for x in data["admins"]:
        text += f"• {x}\n"

    await update.message.reply_text(text)


# Ban
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    if user not in data["admins"] and user not in data["founders"]:
        return

    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user.id
        await context.bot.ban_chat_member(update.effective_chat.id, target)

        if target not in data["banned"]:
            data["banned"].append(target)
            save_data(data)

        await update.message.reply_text("Kullanıcı banlandı.")


# Unban
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    if user not in data["admins"] and user not in data["founders"]:
        return

    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user.id
        await context.bot.unban_chat_member(update.effective_chat.id, target)

        await update.message.reply_text("Ban kaldırıldı.")


# Koruma modu
async def koruma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id

    if user not in data["founders"]:
        return

    data["protection"] = not data["protection"]
    save_data(data)

    await update.message.reply_text(
        f"Koruma modu: {'Aktif' if data['protection'] else 'Kapalı'}"
    )


# Hoşgeldin
async def hosgeldin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        await update.message.reply_text(
            f"""
𖤐 YAHUDA #KABİLE

Hoş geldin {user.first_name}

Kurallar basit:
İtaat et.
Saygı göster.
Sadık kal.
"""
        )


# Hoşçakal
async def hoscakal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.left_chat_member

    await update.message.reply_text(
        f"{user.first_name} ayrıldı.\nKabile zayıflamaz."
    )


# Ana başlat
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("kurucu", kurucu))
    app.add_handler(CommandHandler("yetkiver", yetki_ver))
    app.add_handler(CommandHandler("yetkial", yetki_al))
    app.add_handler(CommandHandler("staff", staff))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("koruma", koruma))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, hosgeldin))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, hoscakal))

    print("YAHUDA #KABİLE AKTİF")
    app.run_polling()


if __name__ == "__main__":
    main()
