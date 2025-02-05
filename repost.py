"""
repost.py - Instagram Reposting Functions
-------------------------------------------
This module provides functions to:
- Log in to Instagram with each user’s destination account credentials.
- Fetch recent media (Reels, Photos, Carousels) from source accounts.
- Repost supported media to the destination account.
- Apply simple anti-detection delays.
"""

import os
import time
import json
import logging
from datetime import datetime
from instagrapi import Client

# Logger setup
logger = logging.getLogger(__name__)

SETTINGS_FILE = "user_settings.json"
if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "r") as file:
        user_settings = json.load(file)
else:
    user_settings = {}

def save_settings():
    """Save updated user settings to file."""
    with open(SETTINGS_FILE, "w") as file:
        json.dump(user_settings, file, indent=4)

def login_instagram(user_id: str):
    """
    Log in to Instagram using the user's destination account credentials.
    Returns an instagrapi Client instance on success.
    """
    settings = user_settings.get(user_id, {})
    client = Client()
    try:
        if settings.get("proxy"):
            client.set_proxy(settings["proxy"])
        client.login(settings["instagram_username"], settings["instagram_password"])
        logger.info("Instagram login successful for user %s", user_id)
    except Exception as e:
        logger.error("Instagram login failed for user %s: %s", user_id, e)
        return None
    return client

def check_and_repost():
    """
    For each user with auto_repost enabled, log in to Instagram,
    check source accounts for new media, and repost supported content.
    """
    for user_id, settings in user_settings.items():
        if not settings.get("auto_repost"):
            continue  # Skip if auto repost is off

        logger.info("Processing repost for user %s", user_id)
        settings["last_repost_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        client = login_instagram(user_id)
        if not client:
            logger.error("Skipping user %s due to login failure", user_id)
            continue

        for source in settings.get("source_accounts", []):
            try:
                # Fetch recent media (latest 5 posts) from the source account
                media_items = client.user_medias_gql(source, 5)
                for media in media_items:
                    media_type = media.media_type  # 1 = Photo, 2 = Video, 8 = Carousel
                    if media_type == 1 and not settings["supported_content"].get("photos", True):
                        continue
                    if media_type == 2 and not settings["supported_content"].get("reels", True):
                        continue
                    if media_type == 8 and not settings["supported_content"].get("carousels", True):
                        continue

                    # Prepare caption
                    caption = media.caption_text if settings.get("use_original_caption") else settings.get("custom_caption", "")

                    # Anti-detection delay (could be randomized)
                    time.sleep(5)

                    # Repost depending on media type
                    if media_type in [1, 8]:
                        filename = client.photo_download(media.pk)
                        client.photo_upload(filename, caption)
                        logger.info("Reposted photo/carousel from %s", source)
                    elif media_type == 2:
                        filename = client.video_download(media.pk)
                        client.video_upload(filename, caption)
                        logger.info("Reposted video (Reel) from %s", source)
            except Exception as e:
                logger.error("Error processing source %s for user %s: %s", source, user_id, e)
        save_settings()
