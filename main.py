import requests
import time
from dotenv import load_dotenv
import os
from datetime import datetime

# ==========================================
# LOAD ENV VARIABLES
# ==========================================

load_dotenv(dotenv_path=".env")

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# ==========================================
# WATCHLIST
# ==========================================

WATCHLIST = {
    "nvidia": "🟢 NVIDIA",
    "tesla": "🔴 TESLA",
    "apple": "🍎 APPLE",
    "microsoft": "🪟 MICROSOFT",
    "amazon": "📦 AMAZON",
    "google": "🔍 GOOGLE",
    "meta": "📘 META",
    "amd": "⚡ AMD",
    "intel": "💻 INTEL",
    "netflix": "🎬 NETFLIX"
}

# ==========================================
# KEYWORD SCORING SYSTEM
# ==========================================

KEYWORD_SCORES = {

    # FED / ECONOMY
    "fed": 6,
    "federal reserve": 6,
    "interest rates": 5,
    "rate cut": 7,
    "rate hike": 7,
    "inflation": 5,
    "cpi": 5,
    "recession": 8,

    # MARKET EVENTS
    "market crash": 9,
    "selloff": 7,
    "rally": 4,
    "surge": 4,
    "plunge": 7,
    "stocks": 2,

    # COMPANY EVENTS
    "earnings": 5,
    "guidance": 4,
    "ipo": 5,
    "merger": 6,
    "acquisition": 6,
    "bankruptcy": 10,

    # TECH / AI
    "ai": 4,
    "chip": 3,
    "semiconductor": 4,
    "gpu": 3,

    # CRYPTO
    "bitcoin": 4,
    "ethereum": 4,

    # RISK
    "lawsuit": 5,
    "investigation": 5,
    "tariffs": 5
}

# ==========================================
# FETCH NEWS
# ==========================================

def fetch_news():

    url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_API_KEY}"

    response = requests.get(url)

    return response.json()

# ==========================================
# CALCULATE SCORE
# ==========================================

def calculate_score(article):

    score = 0

    headline = article.get("headline", "")
    summary = article.get("summary", "")

    text = (headline + " " + summary).lower()

    matched_keywords = []
    matched_stocks = []

    # Keyword scoring
    for keyword, value in KEYWORD_SCORES.items():

        if keyword in text:
            score += value
            matched_keywords.append(keyword)

    # Watchlist boost
    for stock in WATCHLIST:

        if stock in text:
            score += 4
            matched_stocks.append(stock)

    return score, matched_keywords, matched_stocks

# ==========================================
# DUPLICATE CHECK
# ==========================================

def already_sent(url):

    with open("sent_news.txt", "r") as file:

        sent_urls = file.read().splitlines()

    return url in sent_urls

# ==========================================
# SAVE SENT URL
# ==========================================

def save_sent(url):

    with open("sent_news.txt", "a") as file:

        file.write(url + "\n")

# ==========================================
# IMPACT LEVEL
# ==========================================

def get_impact_level(score):

    if score >= 15:
        return "🔥 EXTREME IMPACT"

    elif score >= 10:
        return "🚨 HIGH IMPACT"

    elif score >= 6:
        return "⚠️ MEDIUM IMPACT"

    else:
        return "ℹ️ LOW IMPACT"

# ==========================================
# MARKET INSIGHT
# ==========================================

def generate_market_insight(score, matched_keywords):

    if "rate cut" in matched_keywords:
        return "Rate cuts usually boost growth and technology stocks."

    if "inflation" in matched_keywords:
        return "Inflation data strongly influences Federal Reserve decisions."

    if "earnings" in matched_keywords:
        return "Strong earnings can significantly move stock prices."

    if "market crash" in matched_keywords:
        return "High volatility and fear may spread across markets."

    if "ai" in matched_keywords:
        return "AI-related news is currently a major market driver."

    if score >= 15:
        return "This news may have broad market-wide impact."

    elif score >= 10:
        return "This development could influence multiple sectors."

    elif score >= 6:
        return "Worth monitoring for potential market reactions."

    return "Minor market update."

# ==========================================
# SEND TO DISCORD
# ==========================================

def send_to_discord(article, score, matched_keywords, matched_stocks):

    headline = article.get("headline", "No headline")
    summary = article.get("summary", "No summary")
    url = article.get("url", "")
    source = article.get("source", "Unknown")

    impact = get_impact_level(score)

    insight = generate_market_insight(score, matched_keywords)

    stocks_text = ", ".join(
        [WATCHLIST[stock] for stock in matched_stocks]
    )

    keywords_text = ", ".join(matched_keywords)

    current_time = datetime.now().strftime("%H:%M:%S")

    embed = {
        "title": impact,
        "description": f"## {headline}",
        "url": url,
        "color": 16711680,
        "fields": [
            {
                "name": "📊 Impact Score",
                "value": f"`{score}`",
                "inline": True
            },
            {
                "name": "📰 Source",
                "value": source,
                "inline": True
            },
            {
                "name": "⏰ Time",
                "value": current_time,
                "inline": True
            },
            {
                "name": "📈 Watchlist Stocks",
                "value": stocks_text if stocks_text else "None",
                "inline": False
            },
            {
                "name": "🧠 AI Market Insight",
                "value": insight,
                "inline": False
            },
            {
                "name": "🔑 Matched Keywords",
                "value": keywords_text if keywords_text else "None",
                "inline": False
            },
            {
                "name": "📄 Article Summary",
                "value": summary[:600],
                "inline": False
            }
        ],
        "footer": {
            "text": "Smart Market Intelligence Bot"
        }
    }

    data = {
        "embeds": [embed]
    }

    response = requests.post(DISCORD_WEBHOOK_URL, json=data)

    print("===================================")
    print("DISCORD STATUS:", response.status_code)
    print("HEADLINE:", headline)
    print("SCORE:", score)
    print("KEYWORDS:", matched_keywords)
    print("WATCHLIST:", matched_stocks)
    print("===================================")

# ==========================================
# MAIN LOOP
# ==========================================

print("===================================")
print("SMART MARKET BOT STARTED")
print("24/7 MARKET INTELLIGENCE ACTIVE")
print("===================================")

while True:

    try:

        news = fetch_news()

        for article in news:

            url = article.get("url", "")

            if not url:
                continue

            if already_sent(url):
                continue

            score, matched_keywords, matched_stocks = calculate_score(article)

            headline = article.get("headline", "No headline")

            print("-----------------------------------")
            print("Headline:", headline)
            print("Score:", score)
            print("-----------------------------------")

            # FILTER LOW QUALITY NEWS
            if score < 5:
                continue

            send_to_discord(
                article,
                score,
                matched_keywords,
                matched_stocks
            )

            save_sent(url)

            # Avoid rate limiting
            time.sleep(3)

    except Exception as e:

        print("ERROR:", e)

    # Check every 10 minutes
    time.sleep(600)