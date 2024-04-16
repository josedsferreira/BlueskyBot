#!/usr/bin/env python3

import random
import schedule
import time
import os
import datetime
from datetime import datetime
from bsky_bridge import BskySession
from bsky_bridge import post_text

def prepare_quotes():
    with open('quotes.txt', 'r', encoding='utf-8-sig') as quotesf:
        quotes = quotesf.read().split('%')
        quotes = [q.strip() for q in quotes] #clean up quotes
        with open('preparedQuotes.txt', 'w', encoding='utf-8-sig') as newQuotesf:
            for quote in quotes:
                if len(quote) < 300:
                    newQuotesf.write(quote + '%')

def get_random_quote():
    try:
        with open('preparedQuotes.txt', 'r', encoding='utf-8-sig') as quotesf:
            quotes = quotesf.read().split('%')

        if not quotes:
            print("No quotes available, Boss, restarting...")
            quotesf.close()
            prepare_quotes()
            return get_random_quote()  # Recursive call to get a quote from the newly prepared file

        random_quote = random.choice(quotes)

        # Remove the quote from the list
        quotes.remove(random_quote)

        with open('preparedQuotes.txt', 'w', encoding='utf-8-sig') as quotesf:
            quotesf.write('%'.join(quotes))

        return random_quote

    except FileNotFoundError:
        print("Couldn't find the file, Boss.")

def post_to_bluesky():
    bluesky_username = 'josedsferreira@gmail.com'
    bluesky_password = os.getenv('bs_pw')
    """
    To safely insert password, run the following command in
    the terminal before running this script:
    if you are using linux: export bs_pw="your password here"
    if you are using windows: set bs_pw="your password here"
    """
    quote = get_random_quote()
    session = BskySession(bluesky_username, bluesky_password)
    post = post_text(session, quote)
    now = datetime.now()
    print(f"Boss, task accomplished at {now.strftime('%H:%M')}!")

now = datetime.now()
print(f"Boss, starting operation at {now.strftime('%H:%M')}...")
prepare_quotes()

# Schedule the post_to_bluesky function to run at a specific time
sleepTime = 60 #seconds
scheduledTime = "18:30"
schedule.every().day.at(scheduledTime).do(post_to_bluesky)

while True:
    # Check whether a scheduled task is pending to run or not
    schedule.run_pending()
    time.sleep(sleepTime)
    #now = datetime.now()
    #print(f"Boss, checking for scheduled tasks at {now.strftime('%H:%M')}...")
