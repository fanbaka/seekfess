from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
import json
import logging
import re
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Token dan Channel
BOT_TOKEN = '7823671143:AAElw_lSEGg_-16WWirC3MvaW4m4L1ZvBzY'
CHANNEL_ID = '@huntfess'  # Ganti dengan username channel kamu
ADMIN_GROUP_ID = -1001415535129  # Ganti dengan ID grup admin kamu

# Inisialisasi logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

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
    if update.effective_chat.type != "private":
        return

    user_id = update.effective_user.id

    username = update.effective_user.username
    first_name = update.effective_user.first_name
    display_name = f"@{username}" if username else first_name

    if not await check_subscription(user_id, context):
        keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_ID[1:]}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Kamu belum subscribe channel kami. Silakan subscribe di sini:", reply_markup=reply_markup)
        return
    
    is_direct_forward = update.message.text and (update.message.text.startswith("#hunt") or update.message.text.startswith("❄️"))
    target_chat_id = CHANNEL_ID if is_direct_forward else ADMIN_GROUP_ID
    caption = update.message.caption or ""

    if not is_direct_forward:
        caption = f"📩 Pesan dari {display_name} (ID: {user_id}):\n\n" + (caption or "")

    message_sent = None
    if update.message.text:
        text_message = update.message.text if is_direct_forward else f"📩 Pesan dari {display_name} (ID: {user_id}):\n\n{update.message.text}"
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
    
    if is_direct_forward:
        # Menambahkan tombol dengan link menuju pesan yang baru saja dikirim
        keyboard = [[InlineKeyboardButton("Lihat Pesan Kamu", url=f"https://t.me/{CHANNEL_ID[1:]}/{message_sent.message_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Pesan kamu telah dikirim ke channel kami. Kamu dapat melihatnya melalui tombol berikut:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Pesan kamu telah dikirim, mohon tunggu beberapa saat.")

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

async def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.ALL & filters.ChatType.PRIVATE, handle_pesan))
    application.add_handler(MessageHandler(filters.ALL & filters.Chat(ADMIN_GROUP_ID), handle_admin_reply))


    application.run_polling()

if __name__ == '__main__':
    main()
