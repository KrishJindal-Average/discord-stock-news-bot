
import requests
import time
import os
import json
import hashlib
import platform
import feedparser

from datetime import datetime
from dotenv import load_dotenv

# =========================================================
# SMART MARKET TERMINAL v5.0
# =========================================================
# FEATURES:
#
# ✅ Real Market News
# ✅ Political + Economic News
# ✅ RSS Intelligence System
# ✅ Duplicate Detection
# ✅ Sentiment Engine
# ✅ Sector Detection
# ✅ Market Risk Engine
# ✅ Live Stock Prices
# ✅ Beautiful Discord Embeds
# ✅ Breaking News Detection
# ✅ Market Intelligence Engine
# ✅ Railway 24/7 Compatible
# ✅ Bloomberg-style Alerts
#
# =========================================================

# =========================================================
# LOAD ENV VARIABLES
# =========================================================

load_dotenv(dotenv_path=".env")

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# =========================================================
# CONFIGURATION
# =========================================================

CHECK_INTERVAL = 30
ARTICLE_COOLDOWN = 2
MINIMUM_SCORE = 18
CACHE_LIMIT = 1500
MAX_SUMMARY_LENGTH = 900
POST_WINDOW_SECONDS = 2 * 60 * 60
MAX_POSTS_PER_WINDOW = 5

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
    "bitcoin": "₿ BITCOIN",
    "ethereum": "⟠ ETHEREUM"

}

# =========================================================
# STOCK TICKERS
# =========================================================

STOCK_TICKERS = {

    "nvidia": "NVDA",
    "tesla": "TSLA",
    "apple": "AAPL",
    "microsoft": "MSFT",
    "amazon": "AMZN",
    "google": "GOOGL",
    "meta": "META",
    "amd": "AMD",
    "intel": "INTC",
    "bitcoin": "BINANCE:BTCUSDT"

}

# =========================================================
# RSS SOURCES
# =========================================================

RSS_FEEDS = [

    # INDIA: Market-moving business feeds
    "https://timesofindia.indiatimes.com/rssfeeds/1898055.cms",
    "https://www.thehindu.com/business/feeder/default.rss",
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://www.business-standard.com/rss/news.xml",

    # GLOBAL: High-impact financial feeds
    "https://feeds.reuters.com/reuters/businessNews",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html"

]

# =========================================================
# TRUSTED SOURCES
# =========================================================

TRUSTED_SOURCES = {

    "Reuters": 12,
    "Bloomberg": 12,
    "CNBC": 10,
    "Financial Times": 12,
    "The Hindu": 10,
    "The Times of India": 9,
    "Economic Times": 11,
    "MarketWatch": 8

}

# =========================================================
# KEYWORD ENGINE
# =========================================================

KEYWORD_SCORES = {

    # FED / ECONOMY
    "fed": 20,
    "federal reserve": 20,
    "inflation": 18,
    "interest rates": 18,
    "rate cut": 25,
    "rate hike": 25,
    "recession": 30,

    # MARKET EVENTS
    "market crash": 40,
    "selloff": 20,
    "surge": 10,
    "rally": 10,
    "record high": 12,
    "plunge": 22,

    # COMPANY EVENTS
    "earnings": 15,
    "guidance": 12,
    "ipo": 12,
    "merger": 20,
    "acquisition": 20,
    "bankruptcy": 35,

    # AI
    "ai": 12,
    "chip": 10,
    "semiconductor": 14,
    "gpu": 10,

    # CRYPTO
    "bitcoin": 15,
    "crypto": 15,
    "etf": 12,

    # POLITICAL
    "war": 35,
    "sanctions": 25,
    "tariffs": 20,
    "china": 10,
    "rbi": 20,
    "budget": 18,
    "oil": 18,
    "crude": 18

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
    "optimistic"

]

BEARISH_WORDS = [

    "drop",
    "crash",
    "selloff",
    "weak",
    "recession",
    "bankruptcy",
    "fear",
    "decline",
    "plunge",
    "panic"

]

# =========================================================
# CACHE SYSTEM
# =========================================================

CACHE_FILE = "sent_news.json"

def load_cache():

    if not os.path.exists(CACHE_FILE):

        with open(CACHE_FILE, "w") as file:

            json.dump([], file)

    try:

        with open(CACHE_FILE, "r") as file:

            return json.load(file)

    except:

        return []

def save_cache(cache):

    with open(CACHE_FILE, "w") as file:

        json.dump(cache, file)


def prune_post_history(post_timestamps):

    cutoff = time.time() - POST_WINDOW_SECONDS

    return [ts for ts in post_timestamps if ts >= cutoff]

# =========================================================
# HASH SYSTEM
# =========================================================

def generate_hash(text):

    normalized = (
        text.lower()
        .replace(",", "")
        .replace(".", "")
        .replace(":", "")
        .replace("-", "")
        .strip()
    )

    return hashlib.md5(
        normalized.encode()
    ).hexdigest()

# =========================================================
# FETCH MARKET NEWS
# =========================================================

def fetch_market_news():

    all_news = []

    symbols = [

        "AAPL",
        "MSFT",
        "NVDA",
        "TSLA",
        "AMZN",
        "META",
        "AMD",
        "GOOGL",
        "BTCUSD"

    ]

    today = datetime.now().strftime("%Y-%m-%d")

    for symbol in symbols:

        try:

            print(f"Fetching {symbol} news...")

            url = (
                "https://finnhub.io/api/v1/company-news"
                f"?symbol={symbol}"
                f"&from={today}"
                f"&to={today}"
                f"&token={FINNHUB_API_KEY}"
            )

            response = requests.get(
                url,
                timeout=5
            )

            data = response.json()

            if isinstance(data, list):

                all_news.extend(data[:5])

        except Exception as e:

            print(
                f"MARKET NEWS ERROR ({symbol}):",
                e
            )

    return all_news

# =========================================================
# FETCH RSS NEWS
# =========================================================

def fetch_rss_news():

    rss_articles = []

    for feed_url in RSS_FEEDS:

        try:

            print(f"Fetching RSS: {feed_url}")

            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:5]:

                rss_articles.append({

                    "headline": entry.title,

                    "summary": getattr(
                        entry,
                        "summary",
                        ""
                    ),

                    "url": entry.link,

                    "source": (
                        feed.feed.title
                        if hasattr(feed, "feed")
                        else "RSS Feed"
                    ),

                    "image": ""

                })

        except Exception as e:

            print("RSS ERROR:", e)

    return rss_articles

# =========================================================
# FETCH STOCK PRICE
# =========================================================

def fetch_stock_price(symbol):

    try:

        url = (
            "https://finnhub.io/api/v1/quote"
            f"?symbol={symbol}"
            f"&token={FINNHUB_API_KEY}"
        )

        response = requests.get(
            url,
            timeout=5
        )

        data = response.json()

        return (
            data.get("c", 0),
            data.get("dp", 0)
        )

    except:

        return None, None

# =========================================================
# DETECT STOCK
# =========================================================

def detect_primary_stock(text):

    text = text.lower()

    for stock, ticker in STOCK_TICKERS.items():

        if stock in text:

            return stock, ticker

    return None, None

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
# DETECT SECTOR
# =========================================================

def detect_sector(text):

    text = text.lower()

    sectors = []

    if any(word in text for word in [
        "nvidia",
        "amd",
        "chip",
        "gpu",
        "semiconductor",
        "ai"
    ]):

        sectors.append(
            "🤖 AI / Semiconductors"
        )

    if any(word in text for word in [
        "tesla",
        "ev",
        "battery"
    ]):

        sectors.append(
            "🚗 Electric Vehicles"
        )

    if any(word in text for word in [
        "fed",
        "inflation",
        "interest rates",
        "recession"
    ]):

        sectors.append(
            "🏦 Macro Economy"
        )

    if any(word in text for word in [
        "bitcoin",
        "crypto",
        "ethereum",
        "etf"
    ]):

        sectors.append(
            "₿ Crypto"
        )

    if not sectors:

        sectors.append(
            "🌍 General Markets"
        )

    return sectors

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

    for keyword, value in KEYWORD_SCORES.items():

        if keyword in text:

            score += value

            matched_keywords.append(
                keyword
            )

    for stock in WATCHLIST:

        if stock in text:

            score += 12

            matched_stocks.append(
                WATCHLIST[stock]
            )

    for trusted, bonus in TRUSTED_SOURCES.items():

        if trusted.lower() in source.lower():

            score += bonus

    score += len(matched_keywords) * 2

    score += len(matched_stocks) * 4

    return (
        score,
        matched_keywords,
        matched_stocks
    )

# =========================================================
# IMPACT LEVEL
# =========================================================

def get_impact_level(score):

    if score >= 70:

        return "☢️ EXTREME MARKET ALERT"

    elif score >= 50:

        return "🔥 CRITICAL MARKET EVENT"

    elif score >= 35:

        return "🚨 HIGH IMPACT NEWS"

    elif score >= 18:

        return "⚠️ IMPORTANT MARKET UPDATE"

    return "ℹ️ LOW PRIORITY"

# =========================================================
# RISK LEVEL
# =========================================================

def get_risk_level(sentiment, score):

    if sentiment == "🔴 Bearish":

        if score >= 50:

            return "🔴 EXTREME RISK"

        return "🟠 HIGH RISK"

    if sentiment == "🟢 Bullish":

        if score >= 50:

            return "🟢 MAJOR OPPORTUNITY"

        return "🟢 POSITIVE"

    return "🟡 NEUTRAL"

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

    if score >= 70:

        analysis.append(
            "Extremely high-impact global market event detected."
        )

    elif score >= 50:

        analysis.append(
            "Critical financial development with strong market-moving potential."
        )

    elif score >= 35:

        analysis.append(
            "Major financial event likely to affect investor sentiment."
        )

    if "war" in keywords:

        analysis.append(
            "Geopolitical tensions may significantly increase market volatility."
        )

    if "inflation" in keywords:

        analysis.append(
            "Inflation expectations could influence central bank policy."
        )

    if "earnings" in keywords:

        analysis.append(
            "Corporate earnings remain a key market catalyst."
        )

    if "rate cut" in keywords:

        analysis.append(
            "Rate cuts are generally supportive for growth equities."
        )

    if "bitcoin" in keywords:

        analysis.append(
            "Crypto markets may experience sharp momentum shifts."
        )

    if sentiment == "🟢 Bullish":

        analysis.append(
            "Current overall sentiment appears bullish."
        )

    elif sentiment == "🔴 Bearish":

        analysis.append(
            "Current overall sentiment appears bearish."
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
    sentiment,
    stock_price,
    stock_change,
    ticker

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

    image = article.get(
        "image",
        ""
    )

    impact = get_impact_level(score)

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

    embed_color = 16711680

    if sentiment == "🟢 Bullish":

        embed_color = 65280

    elif sentiment == "🟡 Neutral":

        embed_color = 16776960

    embed = {

        "title": impact,

        "description":
            f"## 📰 {headline}",

        "url": url,

        "color": embed_color,

        "thumbnail": {

            "url": image

        } if image else {},

        "fields": [

            {
                "name": "📊 Market Impact Score",
                "value": str(score),
                "inline": True
            },

            {
                "name": "📈 Sentiment",
                "value": sentiment,
                "inline": True
            },

            {
                "name": "⚠️ Risk Analysis",
                "value": risk,
                "inline": True
            },

            {
                "name": "💹 Live Market Data",
                "value":

                    f"Ticker: {ticker}\n"
                    f"Price: ${stock_price}\n"
                    f"Daily Change: {stock_change}%"

                if ticker and stock_price

                else "No live stock data",

                "inline": False
            },

            {
                "name": "🌍 Market Sectors",
                "value": "\n".join(sectors),
                "inline": False
            },

            {
                "name": "📈 Watchlist Detection",
                "value":

                    ", ".join(stocks)

                    if stocks else "None",

                "inline": False
            },

            {
                "name": "🔑 Trigger Keywords",
                "value":

                    ", ".join(keywords)

                    if keywords else "None",

                "inline": False
            },

            {
                "name": "🧠 Market Intelligence",
                "value": analysis,
                "inline": False
            },

            {
                "name": "📄 Executive Summary",
                "value":
                    summary[:MAX_SUMMARY_LENGTH],

                "inline": False
            },

            {
                "name": "📰 Source",
                "value": source,
                "inline": True
            },

            {
                "name": "⏰ Scan Time",
                "value": current_time,
                "inline": True
            }

        ],

        "footer": {

            "text":
                "SMART MARKET TERMINAL • LIVE FINANCIAL INTELLIGENCE"

        }

    }

    data = {

        "embeds": [embed]

    }

    response = requests.post(

        DISCORD_WEBHOOK_URL,
        json=data,
        timeout=10

    )

    print("====================================")
    print("ALERT SENT")
    print("Headline:", headline)
    print("Score:", score)
    print("Status:", response.status_code)
    print("====================================")

# =========================================================
# STARTUP MESSAGE
# =========================================================

print("====================================")
print("SMART MARKET TERMINAL ACTIVE")
print("24/7 FINANCIAL INTELLIGENCE ONLINE")
print("====================================")

print(f"System: {platform.system()}")
print(f"Started: {datetime.now()}")
print(f"Scan Interval: {CHECK_INTERVAL} seconds")

print("====================================")

cycle_number = 1
post_timestamps = []

# =========================================================
# MAIN LOOP
# =========================================================

while True:

    try:

        print("\n")
        print("====================================")
        print(f"STARTING MARKET SCAN #{cycle_number}")
        print("====================================")

        cache = load_cache()

        market_news = fetch_market_news()

        rss_news = fetch_rss_news()

        news = market_news + rss_news
        post_timestamps = prune_post_history(post_timestamps)

        if len(post_timestamps) >= MAX_POSTS_PER_WINDOW:

            print(
                "Reached the 2-hour posting limit",
                "– waiting for the next cycle."
            )

            continue

        news = sorted(
            news,
            key=lambda item: calculate_score(item)[0],
            reverse=True
        )

        print(f"Total Articles: {len(news)}")

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

            article_hash = generate_hash(
                headline
            )

            if article_hash in cache:

                continue

            primary_stock, ticker = (
                detect_primary_stock(
                    combined_text
                )
            )

            stock_price = None
            stock_change = None

            if ticker:

                stock_price, stock_change = (
                    fetch_stock_price(
                        ticker
                    )
                )

            score, keywords, stocks = (
                calculate_score(article)
            )

            sentiment = detect_sentiment(
                combined_text
            )

            sectors = detect_sector(
                combined_text
            )

            post_timestamps = prune_post_history(post_timestamps)

            if len(post_timestamps) >= MAX_POSTS_PER_WINDOW:

                print(
                    "Reached the 2-hour posting limit",
                    "during the scan. Skipping remaining articles."
                )

                break

            print("------------------------------------")
            print("Headline:", headline)
            print("Score:", score)
            print("------------------------------------")

            if score < MINIMUM_SCORE:

                continue

            send_to_discord(

                article,
                score,
                keywords,
                stocks,
                sectors,
                sentiment,
                stock_price,
                stock_change,
                ticker

            )

            cache.append(article_hash)
            post_timestamps.append(time.time())

            cache = cache[-CACHE_LIMIT:]

            save_cache(cache)

            time.sleep(ARTICLE_COOLDOWN)

    except Exception as e:

        print("MAIN LOOP ERROR:", e)

    print("====================================")
    print("SCAN COMPLETE")
    print("BOT STILL ACTIVE")
    print("====================================")

    cycle_number += 1

    for remaining in range(
        CHECK_INTERVAL,
        0,
        -1
    ):

        print(
            f"Next market scan in {remaining} seconds...",
            end="\r"
        )

        time.sleep(1)

    print("\nStarting next market scan...")

