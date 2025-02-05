"""
server.py - Dummy Web Server for Heroku & Telegram Bot Starter

This file does two things:
1. Runs a minimal Flask web server that binds to the port Heroku assigns.
2. Starts the Telegram bot (defined in main.py) in a separate thread.
"""

import os
import asyncio
from flask import Flask
import main  # Ensure this imports your Telegram bot's main module

app = Flask(__name__)

@app.route('/')
def index():
    return "Instagram Reposting Bot is running!"

async def run_bot():
    await main.main()

if __name__ == '__main__':
    # Run the bot in the main thread's event loop
    loop = asyncio.get_event_loop()
    loop.create_task(run_bot())

    # Bind to the port assigned by Heroku
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
