# from langchain.tools import tool
import yfinance as yf
import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# @tool
# Done using NEWSAPI.ORG
# def stock_news(symbol: str) -> str:
#     """
#     Get the 7 latest news articles for any stock using NewsAPI.org
#     """
#     API_KEY = os.getenv("NEWS_API_KEY")
#     print(API_KEY)

#     url = "https://newsapi.org/v2/everything"
#     params = {
#         "q": symbol,
#         "sortBy": "publishedAt",
#         "language": "en",
#         "pageSize": 7,
#         "apiKey": API_KEY
#     }

#     try:
#         response = requests.get(url, params=params, timeout=10)
#         data = response.json()

#         if data.get("status") != "ok":
#             return f"NewsAPI Error: {data.get('message')}"

#         articles = data.get("articles", [])
#         simplified = []
#         for a in articles:
#             simplified.append({
#                 "title": a.get("title", "No title"),
#                 "publisher": a.get("source", {}).get("name", "Unknown"),
#                 "publishedAt": a.get("publishedAt", "")[:10],  # YYYY-MM-DD
#                 "link": a.get("url", "")
#             })

#         return json.dumps(simplified, indent=2)

#     except Exception as e:
#         return f"Request failed: {str(e)}"


# @tool
# Done using serper.dev
def stock_news(symbol: str) -> str:
    """
    Get the freshest Google-trending news for any stock using Serper.dev
    """
    api_key = os.getenv("SERPER_API_KEY")

    url = "https://google.serper.dev/news"

    payload = json.dumps({
        "q": f"{symbol} stock news OR earnings OR analyst OR price target -pdf",
        "gl": "us",
        "hl": "en",
        "num": 6
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
        for item in results[:5]:
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


# @tool
# def stock_news(symbol: str) -> str:
#     """ "
#     Get the 10 latest news articles for any stock using Alpaca API
#     """
#     API_KEY = os.getenv("ALPACA_API_KEY")
#     SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")


#     url = f"https://data.alpaca.markets/v1beta1/news?sort=desc&symbols={symbol}"
#     headers = {
#         "APCA-API-KEY-ID": API_KEY,
#         "APCA-API-SECRET-KEY": SECRET_KEY,
#     }

#     r = requests.get(url, headers=headers)
#     data = r.json()

#     return json.dumps(data, indent=2)

if __name__ == "__main__":
    print(stock_news("AAPL"))
