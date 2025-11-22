from langchain.tools import tool
import yfinance as yf
import json

@tool
def price_ohlcv(symbol: str) -> str:
    """
    OHLCV tool using Yahoo Finance.
    Always returns:
    - current_price
    - last 10 intraday 1min candles (if market open)
    - fallback to last 10 daily candles if intraday not available
    """

    symbol = symbol.upper()

    try:
        ticker = yf.Ticker(symbol)

        # Try fetching last 10 1-minute candles
        data = ticker.history(interval="1m", period="1d")

        if data.empty:
            # fallback: 1-day candles (for stocks without intraday)
            data = ticker.history(interval="1d", period="10d")

        if data.empty:
            return json.dumps({"symbol": symbol, "error": "No OHLCV data found."})

        # Take last 10 rows
        last_10 = data.tail(10)

        ohlcv_list = []
        for idx, row in last_10.iterrows():
            ts = idx.to_pydatetime().strftime("%Y-%m-%d %H:%M")

            ohlcv_list.append({
                "time": ts,
                "open": round(row["Open"], 4),
                "high": round(row["High"], 4),
                "low": round(row["Low"], 4),
                "close": round(row["Close"], 4),
                "volume": int(row["Volume"]),
            })

        current_price = ohlcv_list[-1]["close"]

        result = {
            "symbol": symbol,
            "current_price": current_price,
            "1min_ohlcv_last_10": ohlcv_list,
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"symbol": symbol, "error": str(e)})

# if __name__ == "__main__":
#     print(price_ohlcv("AAPL"))