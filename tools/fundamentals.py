from langchain.tools import tool
import yfinance as yf
import json

@tool
def fundamentals(symbol: str) -> str:
    """Get rich fundamental data from Yahoo Finance for deep analysis."""
    ticker = yf.Ticker(symbol)
    info = ticker.info

    fields = {
        # --- Company Info ---
        "longName": "Name",
        "symbol": "Symbol",
        "sector": "Sector",
        "industry": "Industry",
        # --- Valuation ---
        "marketCap": "Market Cap",
        "enterpriseValue": "Enterprise Value",
        "trailingPE": "Trailing P/E",
        "forwardPE": "Forward P/E",
        "pegRatio": "PEG Ratio",
        "priceToSalesTrailing12Months": "Price/Sales",
        "priceToBook": "Price/Book",
        "enterpriseToRevenue": "EV/Revenue",
        "enterpriseToEbitda": "EV/EBITDA",
        # --- Stock Price Info ---
        "currentPrice": "Current Price",
        "targetMedianPrice": "Analyst Median Target",
        "targetHighPrice": "Analyst High Target",
        "targetLowPrice": "Analyst Low Target",
        "recommendationKey": "Analyst Recommendation",
        # --- Profitability & Margins ---
        "profitMargins": "Profit Margin",
        "operatingMargins": "Operating Margin",
        "grossMargins": "Gross Margin",
        "returnOnAssets": "ROA",
        "returnOnEquity": "ROE",
        # --- Growth ---
        "earningsGrowth": "Earnings Growth YoY",
        "revenueGrowth": "Revenue Growth YoY",
        "earningsQuarterlyGrowth": "Quarterly Earnings Growth",
        "revenueQuarterlyGrowth": "Quarterly Revenue Growth",
        # --- Financial Health ---
        "totalCash": "Total Cash",
        "totalCashPerShare": "Cash Per Share",
        "totalDebt": "Total Debt",
        "debtToEquity": "Debt-to-Equity",
        "currentRatio": "Current Ratio",
        "quickRatio": "Quick Ratio",
        # --- Cashflow ---
        "operatingCashflow": "Operating Cashflow",
        "freeCashflow": "Free Cashflow",
        # --- Dividends ---
        "dividendYield": "Dividend Yield",
        "payoutRatio": "Payout Ratio",
        "dividendRate": "Dividend Rate",
        # --- Risk Metrics ---
        "beta": "Beta",
        "heldPercentInsiders": "% Held by Insiders",
        "heldPercentInstitutions": "% Held by Institutions",
        # --- 52W Metrics ---
        "52WeekChange": "52W Change",
        "fiftyTwoWeekHigh": "52W High",
        "fiftyTwoWeekLow": "52W Low",
    }

    output = {}
    for key, label in fields.items():
        output[label] = info.get(key)

    return json.dumps(output, indent=2)


# @tool
# def fundamentals(symbol: str) -> str:
#     """Get key fundamental data from Yahoo Finance."""
#     ticker = yf.Ticker(symbol)
#     info = ticker.info

#     fields = [
#         "longName",
#         "sector",
#         "industry",
#         "marketCap",
#         "trailingPE",
#         "forwardPE",
#         "dividendYield",
#         "profitMargins",
#         "beta",
#         "earningsGrowth",
#         "revenueGrowth",
#     ]

#     output = {k: info.get(k) for k in fields}
#     return json.dumps(output, indent=2)


# if __name__ == "__main__":
#     print(fundamentals("TSLA"))
#     print(fundamentals("FOXX"))
