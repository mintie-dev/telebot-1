import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s\n'
           'User: %(user)s\n'
           'Chat: %(chat)s\n'
           'Action: %(message)s\n'
           '------------------------',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Dictionary to store user data: {user_id: {'first_claim': datetime, 'claims_count': int, 'credits': int}}
user_data = {}

# Helper function to get user info for logging
def get_user_info(update: Update):
    user = update.effective_user
    chat = update.effective_chat
    return {
        'user': f'{user.first_name} ({user.id})',
        'chat': f'{chat.type}: {chat.title if chat.title else "Private"} ({chat.id})'
    }

# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    extra = get_user_info(update)
    logger.info('Command: /start', extra=extra)
    
    chat_type = update.message.chat.type
    if chat_type == 'private':
        await update.message.reply_text('Hello! I am your bot. Use /help to see what I can do.')
    else:
        await update.message.reply_text('Hello! I am your bot. Use /help to see what I can do.\nNote: You can also interact with me in private chat!')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.message.chat.type
    help_text = '''
Available commands:
/start - Start the bot
/help - Show this help message
/dailyclaim - Claim daily credits!
/credits - Check your credit balance
'''
    if chat_type != 'private':
        help_text += '\nTip: You can also message me privately to avoid group chat clutter!'
    
    await update.message.reply_text(help_text)

async def dailyclaim_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    extra = get_user_info(update)
    user_id = update.effective_user.id
    current_time = datetime.now()
    
    # Initialize user data if not exists
    if user_id not in user_data:
        logger.info('New user initialized', extra=extra)
        user_data[user_id] = {
            'first_claim': None,
            'last_period_claimed': None,
            'credits': 0
        }
    
    user = user_data[user_id]
    
    # If this is their first ever claim
    if user['first_claim'] is None:
        logger.info('First time claim', extra=extra)
        user['first_claim'] = current_time
        user['last_period_claimed'] = 0  # Period 0 is claimed
        user['credits'] += 30
        await update.message.reply_text(
            f"First claim successful! You got 30 credits!\nYour balance is: {user['credits']} credits"
        )
        return
     # Calculate which 24h period we're in since first claim
    time_since_first = current_time - user['first_claim']
    current_period = time_since_first.days
    
    # Check if user has claimed during this period
    if user['last_period_claimed'] == current_period:
        logger.info('Attempted to claim too early', extra=extra)
        # Calculate time until next period
        next_period_start = user['first_claim'] + timedelta(days=current_period + 1)
        time_left = next_period_start - current_time
        hours = int(time_left.total_seconds() // 3600)
        minutes = int((time_left.total_seconds() % 3600) // 60)
        await update.message.reply_text(
            f"You've already claimed in this 24h period! Next claim available in {hours}h {minutes}m"
        )
        return
    
    # Give credits and update last claimed period
    logger.info(f'Successful claim. New balance: {user["credits"] + 30}', extra=extra)
    user['credits'] += 30
    user['last_period_claimed'] = current_period
    
    await update.message.reply_text(
        f"You've claimed 30 credits!\nYour new balance is: {user['credits']} credits"
    )

async def credits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Initialize user data if not exists
    if user_id not in user_data:
        user_data[user_id] = {
            'first_claim': None,
            'last_period_claimed': None,
            'credits': 0
        }
    
    credits = user_data[user_id]['credits']
    await update.message.reply_text(f"Your current balance is: {credits} credits")

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only respond to direct messages, not group messages without commands
    if update.message.chat.type == 'private':
        text = update.message.text
        await update.message.reply_text(f'You said: {text}')

def main():
    # Use token from environment variable
    app = Application.builder().token(os.getenv('BOT_TOKEN')).build()

    # Add command handlers
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('dailyclaim', dailyclaim_command))
    app.add_handler(CommandHandler('credits', credits_command))
    # Add message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    print('Starting bot...')
    app.run_polling(poll_interval=3)

if __name__ == '__main__':
    main() 