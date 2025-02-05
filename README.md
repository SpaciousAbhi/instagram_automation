# Instagram Reposting Bot

This repository contains a multi-user Telegram-based Instagram reposting bot. The bot:
- Allows each user to log in interactively with their own Instagram credentials.
- Manages multiple Instagram source accounts per user.
- Supports automated reposting of Reels, Photos, and Carousel posts.
- Offers extensive customization through inline buttons.
- Is ready to deploy on Heroku.

## File Structure

my-instagram-bot/ 
├── main.py # Telegram bot code and inline menus 
├── repost.py # Instagram reposting logic 
├── scheduler.py # Scheduler to run reposting tasks periodically 
├── requirements.txt # Required Python packages 
├── Procfile # Heroku process definitions 
└── README.md # This file
