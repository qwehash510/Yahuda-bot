import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner
from aiogram.utils import executor

# TOKEN (Railway için environment variable önerilir)
TOKEN = os.getenv("BOT_TOKEN") or "TOKEN_BURAYA"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# =========================
# YETKI KONTROL SISTEMI
# =========================

async def is_admin(chat_id, user_id):
    member = await bot.get_chat_member(chat_id, user_id)
    return isinstance(member, (ChatMemberAdministrator, ChatMemberOwner))

async def is_owner(chat_id, user_id):
    member = await bot.get_chat_member(chat_id, user_id)
    return isinstance(member, ChatMemberOwner)

# =========================
# BASLANGIC KOMUTU
# =========================

@dp.message_handler(commands=['start', 'santana'])
async def start_cmd(message: types.Message):
    await message.reply(
        "⚡ Ultimate V8 Bot Aktif\n\n"
        "🛡 Full koruma aktif\n"
        "👑 Yetki sistemi aktif\n"
        "🚀 Santana Ultimate"
    )

# =========================
# YETKI VER
# =========================

@dp.message_handler(commands=['yetkiver'])
async def yetki_ver(message: types.Message):

    if not await is_owner(message.chat.id, message.from_user.id):
        return await message.reply("❌ Sadece kurucu kullanabilir")

    if not message.reply_to_message:
        return await message.reply("Birini yanıtlayarak kullan")

    user_id = message.reply_to_message.from_user.id

    await bot.promote_chat_member(
        chat_id=message.chat.id,
        user_id=user_id,
        can_manage_chat=True,
        can_delete_messages=True,
        can_invite_users=True,
        can_restrict_members=True,
        can_pin_messages=True
    )

    await message.reply("✅ Staff yetkisi verildi")

# =========================
# YETKI AL
# =========================

@dp.message_handler(commands=['yetkial'])
async def yetki_al(message: types.Message):

    if not await is_owner(message.chat.id, message.from_user.id):
        return await message.reply("❌ Sadece kurucu kullanabilir")

    if not message.reply_to_message:
        return await message.reply("Birini yanıtlayarak kullan")

    user_id = message.reply_to_message.from_user.id

    await bot.promote_chat_member(
        chat_id=message.chat.id,
        user_id=user_id,
        can_manage_chat=False,
        can_delete_messages=False,
        can_invite_users=False,
        can_restrict_members=False,
        can_pin_messages=False
    )

    await message.reply("❌ Yetki alındı")

# =========================
# BAN
# =========================

@dp.message_handler(commands=['ban'])
async def ban_user(message: types.Message):

    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply("❌ Admin değilsin")

    if not message.reply_to_message:
        return await message.reply("Birini yanıtla")

    await bot.kick_chat_member(
        message.chat.id,
        message.reply_to_message.from_user.id
    )

    await message.reply("🚫 Kullanıcı banlandı")

# =========================
# MUTE
# =========================

@dp.message_handler(commands=['mute'])
async def mute_user(message: types.Message):

    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply("❌ Admin değilsin")

    if not message.reply_to_message:
        return await message.reply("Birini yanıtla")

    await bot.restrict_chat_member(
        message.chat.id,
        message.reply_to_message.from_user.id,
        permissions=types.ChatPermissions(can_send_messages=False)
    )

    await message.reply("🔇 Kullanıcı susturuldu")

# =========================
# UNMUTE
# =========================

@dp.message_handler(commands=['unmute'])
async def unmute_user(message: types.Message):

    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply("❌ Admin değilsin")

    if not message.reply_to_message:
        return await message.reply("Birini yanıtla")

    await bot.restrict_chat_member(
        message.chat.id,
        message.reply_to_message.from_user.id,
        permissions=types.ChatPermissions(can_send_messages=True)
    )

    await message.reply("🔊 Susturma kaldırıldı")

# =========================
# KORUMA SISTEMI
# =========================

@dp.message_handler(content_types=types.ContentType.NEW_CHAT_MEMBERS)
async def welcome(message: types.Message):

    for user in message.new_chat_members:
        await message.reply(f"👋 Hoşgeldin {user.first_name}")

# =========================
# BOT CALISTIR
# =========================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
