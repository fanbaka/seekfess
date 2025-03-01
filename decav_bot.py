from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
import json
import logging
import re
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Token dan Channel
BOT_TOKEN = '7932656511:AAGqJWjaUtUqms3f4pN2z-qJhbAH0Vsq6QQ'
CHANNEL_ID = '@basepf'  # Ganti dengan username channel kamu
ADMIN_GROUP_ID = -1002393683314  # Ganti dengan ID grup admin kamu
LOG_GROUP_ID = -1002354693758  # Ganti dengan ID grup log kamu

# Inisialisasi logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Status bot (aktif atau tidak)
bot_active = True

async def check_subscription(user_id, context: CallbackContext):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        return False

async def start(update: Update, context: CallbackContext):
    if update.effective_chat.type != "private":
        return

    user_id = update.effective_user.id

    if await check_subscription(user_id, context):
        await update.message.reply_text("Halo! Kamu sudah subscribe channel kami. Silakan kirim pesan!")
    else:
        keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_ID[1:]}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Halo! Kamu perlu subscribe channel kami terlebih dahulu untuk menggunakan bot ini.", reply_markup=reply_markup)

async def handle_pesan(update: Update, context: CallbackContext):
    global bot_active
    if update.effective_chat.type != "private":
        return
    
    if not bot_active:
        await update.message.reply_text("Bot sedang dipause oleh admin.")
        return

    user_id = update.effective_user.id

    username = update.effective_user.username
    first_name = update.effective_user.first_name
    display_name = f"@{username}" if username else first_name

    # Cek apakah user sudah subscribe channel
    if not await check_subscription(user_id, context):
        keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_ID[1:]}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Kamu belum subscribe channel kami. Silakan subscribe di sini.", reply_markup=reply_markup)
        return

    # Cek apakah pesan mengandung #hunt atau 🐿 di teks atau caption media
    text_content = (update.message.text or update.message.caption or "").strip().lower()
    is_direct_forward = "#pf" in text_content or "🐿" in text_content

    # Tentukan target kiriman
    target_chat_id = CHANNEL_ID if is_direct_forward else ADMIN_GROUP_ID
    caption = update.message.caption or ""

    # Tambahkan info pengirim jika pesan dikirim ke grup admin
    if not is_direct_forward:
        caption = f"""
        📩 Pesan dari {display_name}
        ID: {user_id}

        {caption if caption else ""}
        """.strip()


    message_sent = None

    # Kirim pesan berdasarkan jenis media
    if update.message.text:

        text_message = (
            update.message.text if is_direct_forward else 
            f"📩 Pesan dari: {first_name}\n"
            f"👤 Username: {display_name}\n"
            f"🆔 ID: {user_id}\n\n"
            f"💬 Pesan:\n{update.message.text or ''}"
        )

        message_sent = await context.bot.send_message(chat_id=target_chat_id, text=text_message)
    elif update.message.photo:
        message_sent = await context.bot.send_photo(chat_id=target_chat_id, photo=update.message.photo[-1].file_id, caption=caption)
    elif update.message.video:
        message_sent = await context.bot.send_video(chat_id=target_chat_id, video=update.message.video.file_id, caption=caption)
    elif update.message.document:
        message_sent = await context.bot.send_document(chat_id=target_chat_id, document=update.message.document.file_id, caption=caption)
    elif update.message.sticker:
        message_sent = await context.bot.send_sticker(chat_id=target_chat_id, sticker=update.message.sticker.file_id)
    elif update.message.audio:
        message_sent = await context.bot.send_audio(chat_id=target_chat_id, audio=update.message.audio.file_id, caption=caption)
    elif update.message.voice:
        message_sent = await context.bot.send_voice(chat_id=target_chat_id, voice=update.message.voice.file_id, caption=caption)
    else:
        await update.message.reply_text("Tipe pesan tidak didukung.")
        return

    # Jika pesan dikirim ke channel, tambahkan tombol untuk melihat pesan
    if is_direct_forward and message_sent:
        keyboard = [[InlineKeyboardButton("Lihat Pesan Kamu", url=f"https://t.me/{CHANNEL_ID[1:]}/{message_sent.message_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Pesan kamu telah dikirim ke channel kami. Kamu dapat melihatnya melalui tombol berikut.", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Pesan kamu telah dikirim, mohon tunggu beberapa saat.")

    # Log masuk ke grup
    if is_direct_forward and message_sent:
        message_link = f"https://t.me/{CHANNEL_ID[1:]}/{message_sent.message_id}"
        log_message = (
            f"📌 Log Menfess:\n"
            f"🕰️ Waktu: {update.message.date}\n"
            f"👤 Pengirim: {display_name}\n"
            f"🆔 ID: {user_id}\n"
            f"💬 Pesan: {update.message.text or 'Media'}"
        )

        log_keyboard = [[InlineKeyboardButton("🔍 Lihat Pesan", url=message_link)]]
        log_markup = InlineKeyboardMarkup(log_keyboard)

        await context.bot.send_message(chat_id=LOG_GROUP_ID, text=log_message, reply_markup=log_markup)


async def handle_admin_reply(update: Update, context: CallbackContext):
    if update.effective_chat.id != ADMIN_GROUP_ID or not update.message.reply_to_message:
        return
    
    original_message = update.message.reply_to_message
    match = re.search(r"ID(?:\s*Pengguna)?:?\s*(\d+)", original_message.text or original_message.caption or "")

    if not match:
        return
    
    user_id = int(match.group(1))
    reply_text = update.message.text or update.message.caption
    
    logger.info(f"Original message: {original_message.text or original_message.caption}")
    logger.info(f"Extracted user ID: {user_id}")

    caption = f"📬 Balasan dari admin:\n\n{reply_text}" if reply_text else "📬 Balasan dari admin."

    try:
        if update.message.text:
            await context.bot.send_message(chat_id=user_id, text=caption)
        elif update.message.photo:
            await context.bot.send_photo(chat_id=user_id, photo=update.message.photo[-1].file_id, caption=caption)
        elif update.message.video:
            await context.bot.send_video(chat_id=user_id, video=update.message.video.file_id, caption=caption)
        elif update.message.document:
            await context.bot.send_document(chat_id=user_id, document=update.message.document.file_id, caption=caption)
        elif update.message.sticker:
            await context.bot.send_sticker(chat_id=user_id, sticker=update.message.sticker.file_id)
        elif update.message.audio:
            await context.bot.send_audio(chat_id=user_id, audio=update.message.audio.file_id, caption=caption)
        elif update.message.voice:
            await context.bot.send_voice(chat_id=user_id, voice=update.message.voice.file_id, caption=caption)
        else:
            await update.message.reply_text("Jenis balasan tidak didukung.")
            return

        await update.message.reply_text("Balasan telah dikirim.")
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        await update.message.reply_text("Gagal mengirim balasan. Pastikan pengguna masih dapat menerima pesan.")

async def open_bot(update: Update, context: CallbackContext):
    global bot_active
    if update.effective_chat.id == ADMIN_GROUP_ID:
        bot_active = True
        await update.message.reply_text("✅ Bot telah diaktifkan kembali.")

async def close_bot(update: Update, context: CallbackContext):
    global bot_active
    if update.effective_chat.id == ADMIN_GROUP_ID:
        bot_active = False
        await update.message.reply_text("⏸️ Bot telah dipause. Kirim /open untuk mengaktifkan kembali.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('open', open_bot))
    application.add_handler(CommandHandler('close', close_bot))
    application.add_handler(MessageHandler(filters.ALL & filters.ChatType.PRIVATE, handle_pesan))
    application.add_handler(MessageHandler(filters.ALL & filters.Chat(ADMIN_GROUP_ID), handle_admin_reply))


    application.run_polling()

if __name__ == '__main__':
    main()
