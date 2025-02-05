"""
server.py - Dummy Web Server for Heroku & Telegram Bot Starter

This file does two things:
1. Runs a minimal Flask web server that binds to the port Heroku assigns.
2. Starts the Telegram bot (defined in main.py) in a separate thread.
"""

import os
import threading
import asyncio
from flask import Flask
import main  # Ensure this is your Telegram bot module

app = Flask(__name__)

@app.route('/')
def index():
    return "Instagram Reposting Bot is running!"

def run_bot():
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Now, run your bot's main function
    main.main()

if __name__ == '__main__':
    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    # Bind to the port assigned by Heroku
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

