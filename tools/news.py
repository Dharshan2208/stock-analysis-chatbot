import os
import json
import requests
from newspaper import Article, ArticleException
from typing import List, Dict, Any
import time
from datetime import datetime,timedelta
from dotenv import load_dotenv
from langchain.tools import tool

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def fetch_article_text(url: str, timeout: int = 15) -> str:
    """Extract clean readable text from a news URL using newspaper3k"""
    try:
        article = Article(url, fetch_images=False, request_timeout=timeout)
        article.download()
        if article.download_state != 2:  # ArticleDownloadState.SUCCESS
            return ""
        article.parse()
        text = article.text.strip()
        return text[:15000] if text else ""  # Limit per article to avoid token overflow
    except Exception as e:
        print(f"Failed to parse {url}: {e}")
        return ""

def summarize_with_groq(articles: List[Dict[str, Any]], symbol: str) -> str:
    """Send all article texts to Groq and get a smart consolidated summary"""

    if not articles:
        return "No articles to summarize."

    # Combine all article texts with titles as context
    combined_text = ""
    for i, art in enumerate(articles, 1):
        title = art.get("title", "Untitled")
        text = art.get("full_text", "").strip()
        if text:
            combined_text += f"\n\n--- Article {i}: {title} ---\n{text}\n"

    if not combined_text.strip():
        return "Could not extract full text from any articles."

    # prompt = f"""
    #         You are a senior financial news analyst. Summarize the latest news
    #         about {symbol.upper()} stock in a concise, professional bullet-point format.

    #         Include:
    #         - Key price-moving events (earnings, analyst upgrades/downgrades, M&A, guidance, etc.)
    #         - Important numbers: price targets, EPS, revenue figures, ratings changes
    #         - Any major risks or catalysts mentioned
    #         - Final two-sentence takeaway for investors

    #         Be direct, factual, and avoid fluff.

    #         News articles:
    #         {combined_text[:120000]}
    #         """

    prompt = f"""
            You are a senior financial news analyst. Your job is to extract the most
            investment-relevant information about {symbol.upper()} from the latest news.

            OUTPUT REQUIREMENTS (must follow strictly):
            - Write in clean bullet points.
            - Be factual, concise, and remove all fluff.
            - Only include information that directly affects investor sentiment,
            valuation, fundamentals, guidance, legal issues, or market outlook.

            EXTRACT AND SUMMARIZE (MANDATORY SECTIONS):

            1) **Price-Moving Events**
            - Earnings results (EPS, revenue, YoY growth, margins)
            - Analyst upgrades/downgrades, price-target changes (with numbers)
            - M&A announcements, partnerships, product launches
            - Management changes, guidance updates
            - Major regulatory actions, lawsuits, or compliance issues

            2) **Important Numerical Highlights**
            - EPS figures, revenue numbers, margin % changes
            - Analyst price targets and rating changes
            - Forecasts: future EPS/revenue guidance
            - Any market-impacting metrics mentioned in the articles

            3) **Sentiment Signals (very important for main bot)**
            - Whether headlines are broadly **positive**, **negative**, or **mixed**
            - Tone indicators: strong demand, weakening fundamentals, legal headwinds,
                competitive threats, innovation catalysts, macro impacts, etc.

            4) **Risks & Catalysts**
            - Regulatory probes, lawsuits, supply chain issues
            - Strong product demand, contract wins, new markets, cost-cutting
            - Internal/external issues that may affect price direction

            5) **Investor Takeaway (2 sentences max)**
            - A clear summary of directional sentiment based on the news
            - Should support bullish, bearish, or neutral interpretation

            FORMAT:
            - Bullet points only (except final takeaway)
            - No storytelling. No unnecessary adjectives.
            - Focus ONLY on information that will help a financial AI model determine
            stock sentiment.

            News articles:
            {combined_text[:120000]}
            """

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 1024
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        summary = result["choices"][0]["message"]["content"].strip()
        return summary
    except Exception as e:
        return f"Groq summarization failed: {str(e)}"

def stock_news(symbol: str, recency: str = "past 24 hours") -> str:
    """
    Get the freshest Google-trending news for any stock using Serper.dev
    Timeline : past 24 hours or also can do past week.
    """
    api_key = os.getenv("SERPER_API_KEY")

    url = "https://google.serper.dev/news"

    tbs_map = {
        "past 24 hours": "qdr:d",  # 1 day
        "past week": "qdr:w",      # 1 week
        "past month": "qdr:m"      # 1 month (fallback)
    }
    tbs = tbs_map.get(recency, "qdr:d")

    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    payload = json.dumps({
        "q": f'"{symbol}" (stock OR shares OR earnings OR analyst OR "price target" OR upgrade OR downgrade OR guidance) after:{seven_days_ago} -pdf -site:pdf',
        "gl": "us",
        "hl": "en",
        "num": 7,
        "tbs" : tbs
    })

    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = data.get("news", [])
        if not results:
            return f"No recent news found for {symbol}"

        simplified = []
        for item in results[:7]:
            simplified.append({
                "title": item.get("title", "No title"),
                "source": item.get("source", "Unknown"),
                "date": item.get("date", "No date"),
                "link": item.get("link"),
                "snippet": item.get("snippet", "")[:280] + "..." if item.get("snippet") else ""
            })

        return json.dumps(simplified, indent=2)

    except requests.exceptions.HTTPError as e:
        error_msg = response.json().get("message", str(e))
        return f"Serper API error: {error_msg}"
    except Exception as e:
        return f"Request failed: {str(e)}"

@tool
def new_summariser(symbol: str) -> str:
    """
    1. Get fresh news via Serper
    2. Download full article text from each link
    3. Summarize everything with Groq
    """
    print(f"Fetching latest news for {symbol.upper()}...")
    news_json = stock_news(symbol)

    try:
        news_data = json.loads(news_json)
    except json.JSONDecodeError:
        return f"Failed to parse news: {news_json}"

    if isinstance(news_data, str):
        return news_data

    print(f"Found {len(news_data)} articles. Downloading full text...")
    enriched_articles = []
    for item in news_data:
        url = item.get("link")
        if not url:
            continue
        print(f"   • Fetching: {item['title'][:60]}...")
        full_text = fetch_article_text(url)
        enriched_articles.append({
            "title": item["title"],
            "source": item["source"],
            "link": url,
            "full_text": full_text
        })

        time.sleep(0.5)

    # print("Summarizing with Groq.....")
    final_summary = summarize_with_groq(enriched_articles, symbol)

    return f"""# {symbol.upper()} Stock News Summary :
            {final_summary}
            Sources ({len([a for a in enriched_articles if a['full_text']])}) articles processed successfully):"""+ "\n".join([f"- [{a['title']}]({a['link']}) ({a['source']})" for a in enriched_articles if a['full_text']])


# if __name__ == "__main__":
#     # print(new_summariser("NVDA"))
#     print(new_summariser("TSLA"))