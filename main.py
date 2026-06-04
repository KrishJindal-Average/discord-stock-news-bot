import requests
import time
import os
import json
import hashlib
from datetime import datetime
from dotenv import load_dotenv

# =========================================================
# LOAD ENV VARIABLES
# =========================================================

load_dotenv(dotenv_path=".env")

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# =========================================================
# CONFIGURATION
# =========================================================

MINIMUM_SCORE = 8
CHECK_INTERVAL = 600
ARTICLE_COOLDOWN = 2
MAX_SUMMARY_LENGTH = 600
CACHE_LIMIT = 1000

# =========================================================
# WATCHLIST
# =========================================================

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
    "netflix": "🎬 NETFLIX",
    "bitcoin": "₿ BITCOIN",
    "ethereum": "⟠ ETHEREUM"

}

# =========================================================
# TRUSTED SOURCES
# =========================================================

TRUSTED_SOURCES = {

    "Reuters": 5,
    "Bloomberg": 5,
    "CNBC": 4,
    "MarketWatch": 4,
    "Yahoo": 3,
    "Barrons": 4,
    "Financial Times": 5

}

# =========================================================
# HIGH IMPACT KEYWORDS
# =========================================================

KEYWORD_SCORES = {

    # MACRO
    "fed": 10,
    "federal reserve": 10,
    "inflation": 9,
    "cpi": 8,
    "interest rates": 10,
    "rate cut": 14,
    "rate hike": 14,
    "recession": 15,

    # MARKET EVENTS
    "market crash": 20,
    "selloff": 12,
    "surge": 8,
    "rally": 7,
    "record high": 8,
    "plunge": 14,
    "volatility": 7,

    # COMPANY EVENTS
    "earnings": 10,
    "guidance": 8,
    "ipo": 8,
    "merger": 12,
    "acquisition": 12,
    "bankruptcy": 20,

    # AI / TECH
    "ai": 8,
    "chip": 6,
    "semiconductor": 8,
    "gpu": 6,

    # CRYPTO
    "bitcoin": 8,
    "ethereum": 8,
    "crypto": 8,

    # NEGATIVE EVENTS
    "lawsuit": 8,
    "investigation": 8,
    "tariffs": 6

}

# =========================================================
# SECTOR DETECTION
# =========================================================

SECTOR_KEYWORDS = {

    "AI / Semiconductors": [
        "nvidia",
        "amd",
        "intel",
        "chip",
        "gpu",
        "semiconductor",
        "ai"
    ],

    "Electric Vehicles": [
        "tesla",
        "ev",
        "battery",
        "electric vehicle"
    ],

    "Big Tech": [
        "apple",
        "microsoft",
        "amazon",
        "google",
        "meta"
    ],

    "Banking / Macro": [
        "fed",
        "interest rates",
        "inflation",
        "bank",
        "recession"
    ],

    "Crypto": [
        "bitcoin",
        "ethereum",
        "crypto"
    ]
}

# =========================================================
# SENTIMENT ENGINE
# =========================================================

BULLISH_WORDS = [

    "surge",
    "rally",
    "growth",
    "beats",
    "strong",
    "profit",
    "record high",
    "bullish",
    "expansion",
    "breakthrough",
    "optimistic"

]

BEARISH_WORDS = [

    "drop",
    "crash",
    "selloff",
    "weak",
    "recession",
    "lawsuit",
    "bankruptcy",
    "miss",
    "decline",
    "plunge",
    "fear"

]

# =========================================================
# CACHE SYSTEM
# =========================================================

CACHE_FILE = "sent_news.json"

def load_cache():

    if not os.path.exists(CACHE_FILE):

        with open(CACHE_FILE, "w") as file:

            json.dump([], file)

    with open(CACHE_FILE, "r") as file:

        return json.load(file)

def save_cache(cache):

    with open(CACHE_FILE, "w") as file:

        json.dump(cache, file)

# =========================================================
# HASHING SYSTEM
# =========================================================

def generate_hash(text):

    normalized = (
        text.lower()
        .replace(",", "")
        .replace(".", "")
        .replace(":", "")
        .strip()
    )

    return hashlib.md5(
        normalized.encode()
    ).hexdigest()

# =========================================================
# FETCH NEWS
# =========================================================

def fetch_news():

    url = (
        f"https://finnhub.io/api/v1/news?"
        f"category=general&token={FINNHUB_API_KEY}"
    )

    response = requests.get(url, timeout=20)

    return response.json()

# =========================================================
# DETECT SECTOR
# =========================================================

def detect_sector(text):

    sectors = []

    for sector, keywords in SECTOR_KEYWORDS.items():

        for keyword in keywords:

            if keyword in text.lower():

                sectors.append(sector)
                break

    if not sectors:

        return ["General Market"]

    return sectors

# =========================================================
# DETECT SENTIMENT
# =========================================================

def detect_sentiment(text):

    bullish = 0
    bearish = 0

    text = text.lower()

    for word in BULLISH_WORDS:

        if word in text:

            bullish += 1

    for word in BEARISH_WORDS:

        if word in text:

            bearish += 1

    if bullish > bearish:

        return "🟢 Bullish"

    elif bearish > bullish:

        return "🔴 Bearish"

    return "🟡 Neutral"

# =========================================================
# CALCULATE SCORE
# =========================================================

def calculate_score(article):

    score = 0

    headline = str(
        article.get("headline", "")
    ).lower()

    summary = str(
        article.get("summary", "")
    ).lower()

    source = article.get(
        "source",
        "Unknown"
    )

    text = headline + " " + summary

    matched_keywords = []
    matched_stocks = []

    # KEYWORD ENGINE
    for keyword, value in KEYWORD_SCORES.items():

        if keyword in text:

            score += value
            matched_keywords.append(keyword)

    # WATCHLIST BOOST
    for stock in WATCHLIST:

        if stock in text:

            score += 7
            matched_stocks.append(
                WATCHLIST[stock]
            )

    # SOURCE BOOST
    if source in TRUSTED_SOURCES:

        score += TRUSTED_SOURCES[source]

    # MULTI-KEYWORD BOOST
    score += len(matched_keywords) * 2

    # MULTI-STOCK BOOST
    score += len(matched_stocks) * 3

    return (
        score,
        matched_keywords,
        matched_stocks
    )

# =========================================================
# IMPACT LEVEL
# =========================================================

def get_impact_level(score):

    if score >= 35:

        return "☢️ EXTREME MARKET ALERT"

    elif score >= 25:

        return "🔥 CRITICAL IMPACT"

    elif score >= 18:

        return "🚨 HIGH IMPACT"

    elif score >= 10:

        return "⚠️ MEDIUM IMPACT"

    return "ℹ️ LOW IMPACT"

# =========================================================
# RISK LEVEL
# =========================================================

def get_risk_level(sentiment, score):

    if sentiment == "🔴 Bearish" and score >= 20:

        return "🔴 HIGH RISK"

    elif sentiment == "🟢 Bullish" and score >= 20:

        return "🟢 HIGH OPPORTUNITY"

    elif score >= 10:

        return "🟡 MODERATE"

    return "⚪ LOW"

# =========================================================
# URGENCY LEVEL
# =========================================================

def get_urgency(score):

    if score >= 30:

        return "🚨 IMMEDIATE ATTENTION"

    elif score >= 18:

        return "⚠️ CLOSELY MONITOR"

    return "ℹ️ STANDARD"

# =========================================================
# MARKET ANALYSIS ENGINE
# =========================================================

def generate_market_analysis(
    score,
    sectors,
    sentiment,
    keywords
):

    analysis = []

    if score >= 30:

        analysis.append(
            "Major market-moving development detected."
        )

    elif score >= 20:

        analysis.append(
            "High-impact event with potential broad sector influence."
        )

    elif score >= 10:

        analysis.append(
            "Moderately important financial development."
        )

    # SECTOR ANALYSIS
    if "AI / Semiconductors" in sectors:

        analysis.append(
            "AI and semiconductor sectors may experience elevated volatility."
        )

    if "Electric Vehicles" in sectors:

        analysis.append(
            "EV-related equities could react strongly."
        )

    if "Banking / Macro" in sectors:

        analysis.append(
            "Macro-economic expectations may shift."
        )

    if "Crypto" in sectors:

        analysis.append(
            "Cryptocurrency markets could become volatile."
        )

    # KEYWORD ANALYSIS
    if "earnings" in keywords:

        analysis.append(
            "Corporate earnings remain a primary market catalyst."
        )

    if "inflation" in keywords:

        analysis.append(
            "Inflation data may influence Federal Reserve policy."
        )

    if "rate cut" in keywords:

        analysis.append(
            "Rate cuts are typically supportive for growth assets."
        )

    if "recession" in keywords:

        analysis.append(
            "Recession fears may increase defensive positioning."
        )

    # SENTIMENT
    if sentiment == "🟢 Bullish":

        analysis.append(
            "Overall sentiment appears bullish."
        )

    elif sentiment == "🔴 Bearish":

        analysis.append(
            "Overall sentiment appears bearish."
        )

    else:

        analysis.append(
            "Market sentiment remains relatively neutral."
        )

    return " ".join(analysis)

# =========================================================
# SEND DISCORD ALERT
# =========================================================

def send_to_discord(
    article,
    score,
    keywords,
    stocks,
    sectors,
    sentiment
):

    headline = article.get(
        "headline",
        "No headline"
    )

    summary = article.get(
        "summary",
        "No summary"
    )

    source = article.get(
        "source",
        "Unknown"
    )

    url = article.get(
        "url",
        ""
    )

    impact = get_impact_level(score)

    urgency = get_urgency(score)

    risk = get_risk_level(
        sentiment,
        score
    )

    analysis = generate_market_analysis(
        score,
        sectors,
        sentiment,
        keywords
    )

    current_time = datetime.now().strftime(
        "%H:%M:%S"
    )

    embed = {

        "title": impact,

        "description": f"## {headline}",

        "url": url,

        "color": 16724787,

        "fields": [

            {
                "name": "📊 Impact Score",
                "value": str(score),
                "inline": True
            },

            {
                "name": "📈 Sentiment",
                "value": sentiment,
                "inline": True
            },

            {
                "name": "⚠️ Risk Level",
                "value": risk,
                "inline": True
            },

            {
                "name": "🚨 Urgency",
                "value": urgency,
                "inline": False
            },

            {
                "name": "📂 Sectors",
                "value": ", ".join(sectors),
                "inline": False
            },

            {
                "name": "📈 Watchlist Hits",
                "value": ", ".join(stocks)
                if stocks else "None",
                "inline": False
            },

            {
                "name": "🔑 Trigger Keywords",
                "value": ", ".join(keywords)
                if keywords else "None",
                "inline": False
            },

            {
                "name": "🧠 Market Intelligence",
                "value": analysis,
                "inline": False
            },

            {
                "name": "📄 Article Summary",
                "value": summary[:MAX_SUMMARY_LENGTH],
                "inline": False
            }

        ],

        "footer": {
            "text": f"Smart Market Intelligence • {current_time}"
        }

    }

    data = {
        "embeds": [embed]
    }

    response = requests.post(
        DISCORD_WEBHOOK_URL,
        json=data,
        timeout=20
    )

    print("====================================")
    print("DISCORD STATUS:", response.status_code)
    print("HEADLINE:", headline)
    print("SCORE:", score)
    print("====================================")

# =========================================================
# MAIN LOOP
# =========================================================

print("====================================")
print("SMART MARKET TERMINAL ACTIVE")
print("24/7 FINANCIAL INTELLIGENCE ONLINE")
print("====================================")

while True:

    try:

        cache = load_cache()

        news = fetch_news()

        for article in news:

            headline = article.get(
                "headline",
                ""
            )

            summary = article.get(
                "summary",
                ""
            )

            url = article.get(
                "url",
                ""
            )

            if not url:

                continue

            combined_text = (
                headline + " " + summary
            )

            # HARD FINANCE FILTER
            finance_keywords = [

                "stock",
                "stocks",
                "market",
                "nasdaq",
                "dow",
                "s&p",
                "fed",
                "earnings",
                "shares",
                "investors",
                "inflation",
                "interest rates",
                "crypto",
                "bitcoin",
                "ai",
                "tesla",
                "nvidia",
                "apple",
                "microsoft"

            ]

            if not any(
                word in combined_text.lower()
                for word in finance_keywords
            ):

                continue

            # DUPLICATE DETECTION
            article_hash = generate_hash(
                headline
            )

            if article_hash in cache:

                continue

            score, keywords, stocks = (
                calculate_score(article)
            )

            sectors = detect_sector(
                combined_text
            )

            sentiment = detect_sentiment(
                combined_text
            )

            print("------------------------------------")
            print("Headline:", headline)
            print("Score:", score)
            print("------------------------------------")

            # FILTER LOW QUALITY
            if score < MINIMUM_SCORE:

                continue

            send_to_discord(
                article,
                score,
                keywords,
                stocks,
                sectors,
                sentiment
            )

            cache.append(article_hash)

            cache = cache[-CACHE_LIMIT:]

            save_cache(cache)

            time.sleep(ARTICLE_COOLDOWN)

    except Exception as e:

        print("MAIN LOOP ERROR:", e)

    print("Waiting for next cycle...")
    time.sleep(CHECK_INTERVAL)