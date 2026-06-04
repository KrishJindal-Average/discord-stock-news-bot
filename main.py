import requests
import time
import os
import json
import hashlib
import platform
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

CHECK_INTERVAL = 30
ARTICLE_COOLDOWN = 2
MINIMUM_SCORE = 15
CACHE_LIMIT = 1000
MAX_SUMMARY_LENGTH = 700

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
    "netflix": "NFLX",
    "bitcoin": "BINANCE:BTCUSDT"

}

# =========================================================
# TRUSTED SOURCES
# =========================================================

TRUSTED_SOURCES = {

    "Reuters": 8,
    "Bloomberg": 8,
    "CNBC": 6,
    "MarketWatch": 5,
    "Barrons": 7,
    "Financial Times": 8,
    "Yahoo": 4,
    "The Wall Street Journal": 8

}

# =========================================================
# HIGH IMPACT KEYWORDS
# =========================================================

KEYWORD_SCORES = {

    # FED / MACRO
    "fed": 15,
    "federal reserve": 15,
    "inflation": 12,
    "cpi": 10,
    "interest rates": 14,
    "rate cut": 18,
    "rate hike": 18,
    "recession": 20,

    # MARKET
    "market crash": 30,
    "selloff": 18,
    "surge": 8,
    "rally": 7,
    "record high": 10,
    "plunge": 20,
    "volatility": 8,

    # COMPANY EVENTS
    "earnings": 14,
    "guidance": 10,
    "ipo": 10,
    "merger": 16,
    "acquisition": 16,
    "bankruptcy": 25,

    # TECH / AI
    "ai": 10,
    "chip": 8,
    "semiconductor": 10,
    "gpu": 8,

    # CRYPTO
    "bitcoin": 10,
    "ethereum": 10,
    "crypto": 10,
    "etf": 10,

    # NEGATIVE
    "lawsuit": 10,
    "investigation": 10,
    "tariffs": 8

}

# =========================================================
# SECTOR DETECTION
# =========================================================

SECTOR_KEYWORDS = {

    "AI / Semiconductors": [
        "nvidia",
        "amd",
        "intel",
        "gpu",
        "chip",
        "semiconductor",
        "ai"
    ],

    "Electric Vehicles": [
        "tesla",
        "ev",
        "battery"
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
        "inflation",
        "interest rates",
        "recession"
    ],

    "Crypto": [
        "bitcoin",
        "ethereum",
        "crypto",
        "etf"
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

    try:

        with open(CACHE_FILE, "r") as file:

            return json.load(file)

    except:

        return []

def save_cache(cache):

    with open(CACHE_FILE, "w") as file:

        json.dump(cache, file)

# =========================================================
# HASH GENERATOR
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
# FETCH HIGH QUALITY NEWS
# =========================================================

def fetch_news():

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

            url = (
                "https://finnhub.io/api/v1/company-news"
                f"?symbol={symbol}"
                f"&from={today}"
                f"&to={today}"
                f"&token={FINNHUB_API_KEY}"
            )

            response = requests.get(
                url,
                timeout=15
            )

            data = response.json()

            if isinstance(data, list):

                all_news.extend(data[:8])

        except Exception as e:

            print(
                f"NEWS FETCH ERROR ({symbol}):",
                e
            )

    return all_news

# =========================================================
# FETCH LIVE STOCK PRICE
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
            timeout=10
        )

        data = response.json()

        current_price = data.get("c", 0)
        change_percent = data.get("dp", 0)

        return current_price, change_percent

    except:

        return None, None

# =========================================================
# DETECT PRIMARY STOCK
# =========================================================

def detect_primary_stock(text):

    text = text.lower()

    for stock, ticker in STOCK_TICKERS.items():

        if stock in text:

            return stock, ticker

    return None, None

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

    for keyword, value in KEYWORD_SCORES.items():

        if keyword in text:

            score += value
            matched_keywords.append(keyword)

    for stock in WATCHLIST:

        if stock in text:

            score += 10
            matched_stocks.append(
                WATCHLIST[stock]
            )

    if source in TRUSTED_SOURCES:

        score += TRUSTED_SOURCES[source]

    score += len(matched_keywords) * 2

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

    if score >= 50:

        return "☢️ EXTREME MARKET ALERT"

    elif score >= 35:

        return "🔥 CRITICAL IMPACT"

    elif score >= 25:

        return "🚨 HIGH IMPACT"

    elif score >= 15:

        return "⚠️ MEDIUM IMPACT"

    return "ℹ️ LOW IMPACT"

# =========================================================
# RISK LEVEL
# =========================================================

def get_risk_level(sentiment, score):

    if sentiment == "🔴 Bearish" and score >= 30:

        return "🔴 HIGH RISK"

    elif sentiment == "🟢 Bullish" and score >= 30:

        return "🟢 HIGH OPPORTUNITY"

    elif score >= 15:

        return "🟡 MODERATE"

    return "⚪ LOW"

# =========================================================
# MARKET INTELLIGENCE ENGINE
# =========================================================

def generate_market_analysis(
    score,
    sectors,
    sentiment,
    keywords
):

    analysis = []

    if score >= 50:

        analysis.append(
            "Extremely high-impact market event detected."
        )

    elif score >= 35:

        analysis.append(
            "Critical financial development with possible broad market impact."
        )

    elif score >= 25:

        analysis.append(
            "High-impact market event detected."
        )

    if "AI / Semiconductors" in sectors:

        analysis.append(
            "AI and semiconductor equities may experience elevated volatility."
        )

    if "Electric Vehicles" in sectors:

        analysis.append(
            "EV sector momentum may shift significantly."
        )

    if "Banking / Macro" in sectors:

        analysis.append(
            "Macro-economic expectations and interest-rate outlook could change."
        )

    if "Crypto" in sectors:

        analysis.append(
            "Cryptocurrency markets may react aggressively."
        )

    if "earnings" in keywords:

        analysis.append(
            "Corporate earnings remain a major market catalyst."
        )

    if "inflation" in keywords:

        analysis.append(
            "Inflation data may influence Federal Reserve decisions."
        )

    if "rate cut" in keywords:

        analysis.append(
            "Rate cuts are generally supportive for growth assets."
        )

    if "recession" in keywords:

        analysis.append(
            "Recession concerns may trigger defensive positioning."
        )

    if sentiment == "🟢 Bullish":

        analysis.append(
            "Overall sentiment currently appears bullish."
        )

    elif sentiment == "🔴 Bearish":

        analysis.append(
            "Overall sentiment currently appears bearish."
        )

    else:

        analysis.append(
            "Overall market sentiment remains neutral."
        )

    return " ".join(analysis)

# =========================================================
# SEND TO DISCORD
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

    embed = {

        "title": impact,

        "description": f"## {headline}",

        "url": url,

        "color": 16724787,

        "thumbnail": {
            "url": image
        } if image else {},

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
                "name": "📈 Live Market Data",
                "value":
                    f"{ticker}\n"
                    f"💲 {stock_price}\n"
                    f"📊 {stock_change}%",
                "inline": False
            } if ticker and stock_price else {
                "name": "📈 Live Market Data",
                "value": "Unavailable",
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
            "text":
                f"Smart Market Terminal • {current_time}"
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
# STARTUP MESSAGE
# =========================================================

print("====================================")
print("SMART MARKET TERMINAL ACTIVE")
print("24/7 FINANCIAL INTELLIGENCE ONLINE")
print("====================================")

print(f"System: {platform.system()}")
print(f"Started: {datetime.now()}")
print(f"Check Interval: {CHECK_INTERVAL} seconds")

print("====================================")

cycle_number = 1

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

            # FINANCE FILTER
            finance_keywords = [

                "stocks",
                "shares",
                "wall street",
                "market",
                "nasdaq",
                "dow",
                "s&p",

                "fed",
                "federal reserve",
                "inflation",
                "interest rates",
                "recession",
                "economy",

                "earnings",
                "guidance",
                "revenue",
                "profit",
                "ipo",
                "merger",
                "acquisition",

                "ai",
                "chip",
                "semiconductor",
                "gpu",

                "nvidia",
                "tesla",
                "apple",
                "microsoft",
                "amazon",
                "google",
                "meta",
                "amd",
                "intel",

                "bitcoin",
                "ethereum",
                "crypto",
                "etf"

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

            # DETECT STOCK
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

    print("\nStarting new market scan...")