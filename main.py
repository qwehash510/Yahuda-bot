import logging
import json
import os
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("8317082439:AAE5vuI6Agf6EjqEUSsg5_LK2hSZ--GxZlI")

logging.basicConfig(level=logging.INFO)

ROLES_FILE = "roles.json"

# Rolleri yükle
def load_roles():
    if not os.path.exists(ROLES_FILE):
        return {
            "founders": [],
            "cofounders": [],
            "admins": [],
            "mods": [],
            "mutes": []
        }
    with open(ROLES_FILE, "r") as f:
        return json.load(f)

# Rolleri kaydet
def save_roles(data):
    with open(ROLES_FILE, "w") as f:
        json.dump(data, f)

roles = load_roles()

# Rol kontrol
def get_role(user_id):
    if user_id in roles["founders"]:
        return "KURUCU"
    if user_id in roles["cofounders"]:
        return "YARDIMCI KURUCU"
    if user_id in roles["admins"]:
        return "ADMIN"
    if user_id in roles["mods"]:
        return "MOD"
    return "ÜYE"

# İlk kurucu otomatik
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if len(roles["founders"]) == 0:
        roles["founders"].append(user_id)
        save_roles(roles)
        await update.message.reply_text(
            "☠ YAHUDA #KABİLE SİSTEMİ AKTİF\n\n"
            "⚡ İlk kurucu tanımlandı.\n"
            "🛡 Sistem kontrolü sende."
        )
        return

    role = get_role(user_id)

    await update.message.reply_text(
        f"""
☠ YAHUDA #KABİLE SİSTEMİ

⚡ Rolün: {role}

Komutlar:
/yetki
/staff
"""
    )

# Hoş geldin
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:

        msg = f"""
╔══════════════════╗
☠ YAHUDA #KABİLE
╚══════════════════╝

⚡ Yeni varlık algılandı
👤 {member.first_name}

📡 Kabile ağına bağlandı
🛡 Sistem izliyor...

#YAHUDA #KABİLE
"""
        await update.message.reply_text(msg)

# Hoşçakal
async def bye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = update.message.left_chat_member

    msg = f"""
☠ YAHUDA #KABİLE

❌ Bağlantı kesildi
👤 {member.first_name}

📡 Sistemden silindi

#YAHUDA #KABİLE
"""
    await update.message.reply_text(msg)

# Yetki ver
async def yetki(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id

    if get_role(user) not in ["KURUCU", "YARDIMCI KURUCU"]:
        return

    if update.message.reply_to_message is None:
        return

    target = update.message.reply_to_message.from_user.id

    roles["admins"].append(target)
    save_roles(roles)

    await update.message.reply_text("⚡ Yetki verildi")

# Staff liste
async def staff(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = f"""
☠ YAHUDA #KABİLE STAFF

Kurucu: {len(roles['founders'])}
Yardımcı: {len(roles['cofounders'])}
Admin: {len(roles['admins'])}
Mod: {len(roles['mods'])}
"""
    await update.message.reply_text(msg)

# Anti link
async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "http" in update.message.text:
        user = update.effective_user.id

        if get_role(user) == "ÜYE":
            await update.message.delete()

# Anti flood
users = {}

async def anti_flood(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if user not in users:
        users[user] = 0

    users[user] += 1

    if users[user] > 5:
        await update.message.delete()

# Ana
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("yetki", yetki))
app.add_handler(CommandHandler("staff", staff))

app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, bye))

app.add_handler(MessageHandler(filters.TEXT, anti_link))
app.add_handler(MessageHandler(filters.TEXT, anti_flood))

print("YAHUDA #KABİLE AKTİF")

app.run_polling()
