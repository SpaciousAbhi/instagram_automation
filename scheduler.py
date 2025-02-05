"""
scheduler.py - Scheduler for Reposting Tasks
---------------------------------------------
This script imports the check_and_repost function from repost.py
and uses the schedule library to run it periodically.
"""

import schedule
import time
from repost import check_and_repost

def run_scheduler():
    """
    Schedule check_and_repost to run periodically.
    For demo purposes, this is set to every minute.
    Adjust as needed for production.
    """
    schedule.every(1).minutes.do(check_and_repost)
    while True:
        schedule.run_pending()
        time.sleep(10)

if __name__ == "__main__":
    run_scheduler()
