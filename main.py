import requests
import time
from dotenv import load_dotenv
import os

# =========================
# LOAD ENV VARIABLES
# =========================

load_dotenv(dotenv_path=".env")

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# =========================
# IMPORTANT KEYWORDS
# =========================

IMPORTANT_KEYWORDS = [
    "earnings",
    "fed",
    "inflation",
    "interest rates",
    "rate cut",
    "rate hike",
    "recession",
    "ipo",
    "merger",
    "acquisition",
    "ai",
    "nvidia",
    "tesla",
    "apple",
    "microsoft",
    "amazon",
    "google",
    "meta",
    "stocks",
    "market rally",
    "market crash"
]

# =========================
# FETCH NEWS
# =========================

def fetch_news():

    url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_API_KEY}"

    response = requests.get(url)

    return response.json()

# =========================
# FILTER IMPORTANT NEWS
# =========================

def is_important(article):

    text = (
        article.get("headline", "") +
        " " +
        article.get("summary", "")
    ).lower()

    for keyword in IMPORTANT_KEYWORDS:

        if keyword.lower() in text:
            return True

    return False

# =========================
# CHECK DUPLICATES
# =========================

def already_sent(url):

    with open("sent_news.txt", "r") as file:

        sent_urls = file.read().splitlines()

    return url in sent_urls

# =========================
# SAVE SENT URL
# =========================

def save_sent(url):

    with open("sent_news.txt", "a") as file:

        file.write(url + "\n")

# =========================
# SEND TO DISCORD
# =========================

def send_to_discord(article):

    headline = article.get("headline", "No headline")
    summary = article.get("summary", "No summary")
    url = article.get("url", "")
    source = article.get("source", "Unknown")

    data = {
        "embeds": [
            {
                "title": f"🚨 {headline}",
                "description": summary[:1000],
                "url": url,
                "fields": [
                    {
                        "name": "Source",
                        "value": source,
                        "inline": True
                    }
                ]
            }
        ]
    }

    response = requests.post(DISCORD_WEBHOOK_URL, json=data)

    print("Discord Status:", response.status_code)
    print("Sent:", headline)

# =========================
# MAIN LOOP
# =========================

print("BOT STARTED...")

while True:

    try:

        news = fetch_news()

        for article in news:

            url = article.get("url", "")

            if not url:
                continue

            if already_sent(url):
                continue

            if not is_important(article):
                continue

            send_to_discord(article)

            save_sent(url)

            time.sleep(2)

    except Exception as e:

        print("ERROR:", e)

    # CHECK EVERY 10 MINUTES
    time.sleep(600)