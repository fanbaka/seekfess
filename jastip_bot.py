from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import logging
import re
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import asyncio

# Konfigurasi Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# Token dan Channel
BOT_TOKEN = 'YOUR_BOT_TOKEN'
CHANNEL_ID = '@yourchannel'
ADMIN_GROUP_ID = -123456789  # Ganti dengan ID grup admin kamu

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
        await update.message.reply_text("Halo! Kamu perlu subscribe channel kami terlebih dahulu.", reply_markup=reply_markup)

async def handle_pesan(update: Update, context: CallbackContext):
    if update.effective_chat.type != "private":
        return

    user_id = update.effective_user.id
    if not await check_subscription(user_id, context):
        keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_ID[1:]}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Kamu belum subscribe channel kami.", reply_markup=reply_markup)
        return

    text_message = f"📩 Pesan dari ID {user_id}:\n\n{update.message.text}"
    await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=text_message)
    await update.message.reply_text("Pesan kamu telah dikirim ke admin.")

async def handle_admin_reply(update: Update, context: CallbackContext):
    if update.effective_chat.id != ADMIN_GROUP_ID or not update.message.reply_to_message:
        return

    original_message = update.message.reply_to_message
    match = re.search(r"ID(?:\s*Pengguna)?:?\s*(\d+)", original_message.text or "")
    if not match:
        return
    
    user_id = int(match.group(1))
    reply_text = f"📬 Balasan dari admin:\n\n{update.message.text}"
    try:
        await context.bot.send_message(chat_id=user_id, text=reply_text)
        await update.message.reply_text("Balasan telah dikirim.")
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        await update.message.reply_text("Gagal mengirim balasan.")

async def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_pesan))
    application.add_handler(MessageHandler(filters.TEXT & filters.Chat(ADMIN_GROUP_ID), handle_admin_reply))
    await application.run_polling()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(run_bot())
    app.run(host='0.0.0.0', port=8080)
