"""
main.py - Telegram Bot for Instagram Reposting
------------------------------------------------
This script initializes the Telegram bot that lets you:
- Set your Instagram destination account (interactive login for each user).
- Manage multiple Instagram source accounts.
- Configure reposting settings (auto-repost toggle, caption settings, repost interval).
- Toggle which content types (Reels, Photos, Carousels) to repost.
- View logs and monitor activity.

Before running, install dependencies via requirements.txt.
"""

import os
import json
import logging
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ----------------------------
# SETTINGS STORAGE
# ----------------------------

SETTINGS_FILE = "user_settings.json"
# For demo purposes we use a JSON file. In production, use a secure database.
if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "r") as file:
        user_settings = json.load(file)
else:
    user_settings = {}

def save_settings():
    """Save user settings to the JSON file."""
    with open(SETTINGS_FILE, "w") as file:
        json.dump(user_settings, file, indent=4)

def get_user_settings(user_id: str):
    """Retrieve or initialize settings for a given user."""
    if user_id not in user_settings:
        user_settings[user_id] = {
            "instagram_username": None,         # Destination account username
            "instagram_password": None,         # Destination account password
            "source_accounts": [],              # List of Instagram source accounts
            "auto_repost": False,               # Toggle for auto reposting
            "repost_interval": 1,               # Reposting interval in hours
            "use_original_caption": True,       # Toggle between original and custom caption
            "custom_caption": "",               # Custom caption if needed
            "proxy": None,                      # Optional proxy setting
            "last_repost_time": None,           # Timestamp of last repost
            "supported_content": {              # Content type toggles
                "reels": True,
                "photos": True,
                "carousels": True
            },
            "awaiting_source": False,           # Flag to indicate expecting a new source account
            "awaiting_account": False           # Flag to indicate expecting Instagram credentials
        }
        save_settings()
    return user_settings[user_id]

# ----------------------------
# LOGGER SETUP
# ----------------------------

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ----------------------------
# TELEGRAM HANDLERS
# ----------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /start command handler: Initializes settings and displays the main menu.
    """
    user_id = str(update.effective_user.id)
    get_user_settings(user_id)  # Initialize user settings if not present

    text = (
        "Welcome to the Instagram Reposting Bot!\n\n"
        "Configure your settings using the buttons below:\n"
        "• Add your Instagram destination account (your own login)\n"
        "• Manage Instagram source accounts\n"
        "• Adjust reposting options\n"
        "• Toggle which content types to repost\n"
        "• View logs\n\n"
        "All data is stored per user."
    )
    keyboard = [
        [InlineKeyboardButton("Add Instagram Account", callback_data="add_account")],
        [InlineKeyboardButton("Manage Source Accounts", callback_data="manage_sources")],
        [InlineKeyboardButton("Reposting Settings", callback_data="reposting_settings")],
        [InlineKeyboardButton("Content Types", callback_data="content_types_settings")],
        [InlineKeyboardButton("View Logs", callback_data="view_logs")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles text messages from users.
    Depending on the state, text is used to:
    - Set Instagram destination credentials.
    - Add a new Instagram source account.
    """
    user_id = str(update.effective_user.id)
    settings = get_user_settings(user_id)
    text = update.message.text.strip()

    # If waiting for Instagram credentials (format: username:password)
    if settings.get("awaiting_account", False):
        if ":" in text:
            try:
                username, password = text.split(":", 1)
                settings["instagram_username"] = username.strip()
                settings["instagram_password"] = password.strip()
                settings["awaiting_account"] = False
                save_settings()
                await update.message.reply_text("Instagram destination account set successfully!")
            except Exception as e:
                await update.message.reply_text("Error parsing credentials. Please use the format: username:password")
        else:
            await update.message.reply_text("Invalid format. Use username:password")
        return

    # If waiting for a new source account
    if settings.get("awaiting_source", False):
        source_username = text.strip()
        if source_username not in settings["source_accounts"]:
            settings["source_accounts"].append(source_username)
            save_settings()
            await update.message.reply_text(f"Source account '{source_username}' added successfully!")
        else:
            await update.message.reply_text("This source account already exists.")
        settings["awaiting_source"] = False
        save_settings()
        return

    await update.message.reply_text("Command not recognized. Use the inline buttons to navigate.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles callback queries from inline buttons.
    """
    query = update.callback_query
    user_id = str(query.from_user.id)
    settings = get_user_settings(user_id)
    data = query.data
    await query.answer()  # Acknowledge button press

    # ----- Add Instagram Destination Account -----
    if data == "add_account":
        settings["awaiting_account"] = True
        save_settings()
        await query.edit_message_text(
            "Please send your Instagram destination account credentials in the format:\n\nusername:password"
        )
        return

    # ----- Manage Source Accounts -----
    if data == "manage_sources":
        await manage_sources_menu(query, user_id)
        return

    if data == "add_source":
        settings["awaiting_source"] = True
        save_settings()
        await query.edit_message_text("Please send the Instagram username of the source account to add:")
        return

    if data.startswith("remove_source:"):
        source_to_remove = data.split(":", 1)[1]
        if source_to_remove in settings["source_accounts"]:
            settings["source_accounts"].remove(source_to_remove)
            save_settings()
            await query.edit_message_text(f"Removed source account: {source_to_remove}")
        else:
            await query.edit_message_text("Source account not found.")
        return

    # ----- Reposting Settings Menu -----
    if data == "reposting_settings":
        await reposting_settings_menu(query, user_id)
        return

    if data == "toggle_auto_repost":
        settings["auto_repost"] = not settings["auto_repost"]
        save_settings()
        await reposting_settings_menu(query, user_id)
        return

    if data == "toggle_caption":
        settings["use_original_caption"] = not settings["use_original_caption"]
        save_settings()
        await reposting_settings_menu(query, user_id)
        return

    if data.startswith("set_interval:"):
        interval = int(data.split(":", 1)[1])
        settings["repost_interval"] = interval
        save_settings()
        await reposting_settings_menu(query, user_id)
        return

    # ----- Content Types Settings Menu -----
    if data == "content_types_settings":
        await content_types_settings_menu(query, user_id)
        return

    if data.startswith("toggle_content:"):
        content_type = data.split(":", 1)[1]
        settings["supported_content"][content_type] = not settings["supported_content"][content_type]
        save_settings()
        await content_types_settings_menu(query, user_id)
        return

    # ----- View Logs -----
    if data == "view_logs":
        log_text = "Logs:\n"
        log_text += "Last repost: " + str(settings.get("last_repost_time", "Never"))
        await query.edit_message_text(log_text)
        return

    # ----- Set Interval Menu -----
    if data == "set_interval_menu":
        await set_interval_menu(query)
        return

async def manage_sources_menu(query, user_id: str):
    """Display the menu to manage Instagram source accounts."""
    settings = get_user_settings(user_id)
    keyboard = []
    for source in settings["source_accounts"]:
        keyboard.append([InlineKeyboardButton(f"Remove {source}", callback_data=f"remove_source:{source}")])
    keyboard.append([InlineKeyboardButton("Add New Source Account", callback_data="add_source")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Manage your Instagram source accounts:", reply_markup=reply_markup)

async def reposting_settings_menu(query, user_id: str):
    """Display the reposting settings menu with toggle options."""
    settings = get_user_settings(user_id)
    auto_status = "ON" if settings["auto_repost"] else "OFF"
    caption_status = "Original" if settings["use_original_caption"] else "Custom"
    interval = settings["repost_interval"]
    keyboard = [
        [InlineKeyboardButton(f"Auto-Repost: {auto_status}", callback_data="toggle_auto_repost")],
        [InlineKeyboardButton(f"Caption: {caption_status}", callback_data="toggle_caption")],
        [InlineKeyboardButton(f"Repost Interval: {interval} hour(s)", callback_data="set_interval_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Adjust your reposting settings:", reply_markup=reply_markup)

async def set_interval_menu(query):
    """Display the menu for selecting repost interval."""
    keyboard = [
        [InlineKeyboardButton("1 hour", callback_data="set_interval:1"),
         InlineKeyboardButton("2 hours", callback_data="set_interval:2")],
        [InlineKeyboardButton("3 hours", callback_data="set_interval:3"),
         InlineKeyboardButton("4 hours", callback_data="set_interval:4")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Select your desired repost interval:", reply_markup=reply_markup)

async def content_types_settings_menu(query, user_id: str):
    """Display the menu for toggling supported content types."""
    settings = get_user_settings(user_id)
    keyboard = [
        [InlineKeyboardButton(
            f"Reels: {'ON' if settings['supported_content']['reels'] else 'OFF'}",
            callback_data="toggle_content:reels")],
        [InlineKeyboardButton(
            f"Photos: {'ON' if settings['supported_content']['photos'] else 'OFF'}",
            callback_data="toggle_content:photos")],
        [InlineKeyboardButton(
            f"Carousels: {'ON' if settings['supported_content']['carousels'] else 'OFF'}",
            callback_data="toggle_content:carousels")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Select which content types to repost:", reply_markup=reply_markup)

def main():
    """Initialize and run the Telegram bot."""
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TELEGRAM_TOKEN:
        logger.error("Telegram token not set in environment variables.")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
