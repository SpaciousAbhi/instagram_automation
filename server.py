"""
server.py - Dummy Web Server for Heroku & Telegram Bot Starter

This file does two things:
1. Runs a minimal Flask web server that binds to the port Heroku assigns.
2. Starts the Telegram bot (defined in main.py) in a separate thread.
"""

import os
import threading
from flask import Flask
import main  # This is your Telegram bot module

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def index():
    return "Instagram Reposting Bot is running!"

def run_bot():
    # This function starts your Telegram bot
    main.main()

if __name__ == '__main__':
    # Start the bot in a separate thread so it runs concurrently with the web server
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Bind to the port Heroku provides (or default to 5000)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
