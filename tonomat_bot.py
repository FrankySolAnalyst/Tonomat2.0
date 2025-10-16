import logging
import sqlite3
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Setup logging for debugging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not API_TOKEN:
    logger.error("No TELEGRAM_BOT_TOKEN found in .env file")
    raise ValueError("TELEGRAM_BOT_TOKEN not set in .env file")

# Initialize SQLite database
conn = sqlite3.connect('market.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS items 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, desc TEXT, price REAL, seller_id INTEGER, stock INTEGER DEFAULT 1)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS profiles 
                 (user_id INTEGER PRIMARY KEY, items_sold INTEGER DEFAULT 0, items_bought INTEGER DEFAULT 0)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS orders 
                 (order_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, item_id INTEGER, status TEXT, drop_location TEXT)''')
conn.commit()

# Define custom keyboard
def get_custom_keyboard():
    keyboard = [
        [KeyboardButton("🛒 Shop Now"), KeyboardButton("💰 Deposit")],
        [KeyboardButton("👤 Profile"), KeyboardButton("❓ Help")],
        [KeyboardButton("🚨 SOS"), KeyboardButton("📞 Relatii Clienti")],
        [KeyboardButton("📰 News")]
    ]
    logger.info("Creating custom keyboard: %s", keyboard)
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cursor.execute("INSERT OR IGNORE INTO profiles (user_id) VALUES (?)", (user_id,))
    conn.commit()
    logger.info("Sending /start response to user %s with keyboard", user_id)
    await update.message.reply_text(
        'Welcome to AnonMarket! Use the menu or commands to browse, sell, or manage your profile. 🌟',
        reply_markup=get_custom_keyboard()
    )

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    items = cursor.execute("SELECT id, desc, price, stock FROM items WHERE stock > 0").fetchall()
    if not items:
        logger.info("Shop is empty for user %s", update.effective_user.id)
        await update.message.reply_text(https://github.com/FrankySolAnalyst/Tonomat2.0/blob/main/photos/PozaShopnow.jpg
            "The shop is empty. List an item with /sell! 😞",
            reply_markup=get_custom_keyboard()
        )
        return
    message = "Available products:\n" + "\n".join([f"ID {id}: {desc} - {price} BTC (Stock: {stock})" for id, desc, price, stock in items])
    logger.info("Sending shop items to user %s", update.effective_user.id)
    await update.message.reply_text(
        "Shop-ul dacic 🌿🏛️✨\n" + message + "\n\nUse /buy <item_id> to purchase.",
        reply_markup=get_custom_keyboard()
    )

async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if len(context.args) < 2:
        logger.warning("Invalid /sell command from user %s", user_id)
        await update.message.reply_text(
            "Usage: /sell <description> <price>",
            reply_markup=get_custom_keyboard()
        )
        return
    desc = " ".join(context.args[:-1])
    try:
        price = float(context.args[-1])
        cursor.execute("INSERT INTO items (desc, price, seller_id, stock) VALUES (?, ?, ?, ?)", (desc, price, user_id, 1))
        conn.commit()
        item_id = cursor.lastrowid
        cursor.execute("UPDATE profiles SET items_sold = items_sold + 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        logger.info("Item %s listed by user %s", item_id, user_id)
        await update.message.reply_text(
            f"Item {item_id} listed: {desc} for {price} BTC 🎉",
            reply_markup=get_custom_keyboard()
        )
    except ValueError:
        logger.error("Invalid price format from user %s", user_id)
        await update.message.reply_text(
            "Price must be a number (e.g., /sell Cool Gadget 0.001)",
            reply_markup=get_custom_keyboard()
        )

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if len(context.args) != 1:
        logger.warning("Invalid /buy command from user %s", user_id)
        await update.message.reply_text(
            "Usage: /buy <item_id>",
            reply_markup=get_custom_keyboard()
        )
        return
    try:
        item_id = int(context.args[0])
        item = cursor.execute("SELECT desc, price, stock FROM items WHERE id = ? AND stock > 0", (item_id,)).fetchone()
        if not item:
            logger.warning("Item %s not found or out of stock for user %s", item_id, user_id)
            await update.message.reply_text(
                "Item not found or out of stock. Check /shop for available items. 😞",
                reply_markup=get_custom_keyboard()
            )
            return
        desc, price, stock = item
        # Simulate payment (replace with crypto integration in production)
        cursor.execute("INSERT INTO orders (user_id, item_id, status, drop_location) VALUES (?, ?, ?, ?)",
                      (user_id, item_id, "pending_payment", "40.7128,-74.0060"))  # Dummy coordinates
        cursor.execute("UPDATE items SET stock = stock - 1 WHERE id = ?", (item_id,))
        cursor.execute("UPDATE profiles SET items_bought = items_bought + 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        order_id = cursor.lastrowid
        logger.info("Order %s created for item %s by user %s", order_id, item_id, user_id)
        await update.message.reply_text(
            f"Order {order_id} placed for {desc} ({price} BTC). Send payment to address: [Testnet Address Placeholder]. "
            f"After confirmation, drop location: https://maps.google.com/?q=40.7128,-74.0060",
            reply_markup=get_custom_keyboard()
        )
    except ValueError:
        logger.error("Invalid item ID format from user %s", user_id)
        await update.message.reply_text(
            "Item ID must be a number (e.g., /buy 1)",
            reply_markup=get_custom_keyboard()
        )

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cursor.execute("INSERT OR IGNORE INTO profiles (user_id) VALUES (?)", (user_id,))
    conn.commit()
    stats = cursor.execute("SELECT items_sold, items_bought FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    logger.info("Sending profile stats to user %s", user_id)
    if stats:
        sold, bought = stats
        await update.message.reply_text(
            f"Profile Stats:\nItems Sold: {sold}\nItems Bought: {bought} 😊",
            reply_markup=get_custom_keyboard()
        )
    else:
        await update.message.reply_text(
            "No profile data yet. Start selling or buying! 🚀",
            reply_markup=get_custom_keyboard()
        )

async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Deposit command triggered by user %s", update.effective_user.id)
    await update.message.reply_text(
        "Deposit crypto to buy items. Payment system coming soon (use testnet for thesis). 💸",
        reply_markup=get_custom_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Help command triggered by user %s", update.effective_user.id)
    await update.message.reply_text(
        "AnonMarket Tutorials:\n"
        "/start - Restart the bot\n"
        "/profile - View your stats\n"
        "/shop - Browse products\n"
        "/sell <desc> <price> - List an item\n"
        "/buy <item_id> - Buy an item\n"
        "/deposit - Fund your account\n"
        "/news - Latest updates\n"
        "/sos - Emergency support\n"
        "/relatiiclienti - Customer relations\n"
        "Use the menu button for quick access! ❓",
        reply_markup=get_custom_keyboard()
    )

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("News command triggered by user %s", update.effective_user.id)
    await update.message.reply_text(
        "News: AnonMarket now supports buying! Crypto deposits and dead drops in testing. 📰🎉",
        reply_markup=get_custom_keyboard()
    )

async def sos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("SOS command triggered by user %s", update.effective_user.id)
    await update.message.reply_text(
        "Emergency support: Contact us for urgent issues (details coming soon). 🚨",
        reply_markup=get_custom_keyboard()
    )

async def relatiiclienti(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Relatii Clienti command triggered by user %s", update.effective_user.id)
    await update.message.reply_text(
        "Customer Relations: Reach out for help or feedback (details coming soon). 📞",
        reply_markup=get_custom_keyboard()
    )

async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle menu button clicks by mapping text to commands."""
    text = update.message.text
    logger.info("Received menu button click: %s from user %s", text, update.effective_user.id)
    if text == "🛒 Shop Now":
        await shop(update, context)
    elif text == "👤 Profile":
        await profile(update, context)
    elif text == "💰 Deposit":
        await deposit(update, context)
    elif text == "❓ Help":
        await help_command(update, context)
    elif text == "📰 News":
        await news(update, context)
    elif text == "🚨 SOS":
        await sos(update, context)
    elif text == "📞 Relatii Clienti":
        await relatiiclienti(update, context)
    else:
        logger.warning("Unknown menu button: %s", text)
        await update.message.reply_text(
            "Please use the menu buttons or commands. 😕",
            reply_markup=get_custom_keyboard()
        )

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Menu button triggered by user %s", update.effective_user.id)
    await update.message.reply_text(
        "Please select an option: 🌟",
        reply_markup=get_custom_keyboard()
    )

def main() -> None:
    try:
        # Initialize bot
        application = Application.builder().token(API_TOKEN).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("shop", shop))
        application.add_handler(CommandHandler("sell", sell))
        application.add_handler(CommandHandler("buy", buy))
        application.add_handler(CommandHandler("profile", profile))
        application.add_handler(CommandHandler("deposit", deposit))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("news", news))
        application.add_handler(CommandHandler("sos", sos))
        application.add_handler(CommandHandler("relatiiclienti", relatiiclienti))
        
        # Add message handler for menu buttons
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_buttons))
        
        # Add handler for "Menu" button
        application.add_handler(MessageHandler(filters.Regex("^(Menu)$") & ~filters.COMMAND, handle_menu))
        
        logger.info("Starting bot polling...")
        # Start the bot with polling
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error("Failed to start bot: %s", str(e))
        raise

if __name__ == '__main__':
    main()