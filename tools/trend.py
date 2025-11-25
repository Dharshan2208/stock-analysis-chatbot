from langchain.tools import tool
import yfinance as yf
import json
import numpy as np
from typing import Dict, Any
import pandas as pd

def price_ohlcv_month_hourly(symbol: str) -> str:
    """
    Returns ~1 month (30 days) of 1/2-hour OHLCV data.
    Useful for trend detection and momentum analysis.
    """
    symbol = symbol.upper()

    try:
        ticker = yf.Ticker(symbol)

        # 30 mins interval, last 30 days
        data = ticker.history(interval="30m", period="30d")

        if data.empty:
            return json.dumps(
                {
                    "symbol": symbol,
                    "error": "No hourly data found (invalid symbol or market closed)",
                },
                indent=2,
            )

        # Clean and format
        ohlcv_list = []
        for idx, row in data.iterrows():
            if pd.isna(row["Open"]):
                continue  # skip bad rows

            ts = idx.strftime("%Y-%m-%d %H:%M")

            ohlcv_list.append(
                {
                    "time": ts,
                    "open": round(float(row["Open"]), 4),
                    "high": round(float(row["High"]), 4),
                    "low": round(float(row["Low"]), 4),
                    "close": round(float(row["Close"]), 4),
                    "volume": int(row["Volume"]) if not pd.isna(row["Volume"]) else 0,
                }
            )

        current_price = round(float(data["Close"].iloc[-1]), 4)

        result = {
            "symbol": symbol,
            "current_price": current_price,
            "period": "Last 30 days (1-hour bars)",
            "total_bars": len(ohlcv_list),
            "hourly_ohlcv_1month": ohlcv_list,
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"symbol": symbol, "error": str(e)}, indent=2)

def price_ohlcv_weekly_hourly(symbol: str) -> str:
    """
    Returns last 7 days OHLCV with 1-hour interval.
    Useful for trend detection and momentum analysis.
    """
    symbol = symbol.upper()

    try:
        ticker = yf.Ticker(symbol)
        # 1-hour interval, last 7 days (includes weekends if data available)
        data = ticker.history(interval="1h", period="7d")

        if data.empty:
            return json.dumps(
                {
                    "symbol": symbol,
                    "error": "No hourly OHLCV data found (market closed or invalid symbol?)",
                },
                indent=2,
            )

        ohlcv_list = []
        for idx, row in data.iterrows():
            # Skip rows with NaN values
            if pd.isna(row["Open"]) or pd.isna(row["Volume"]):
                continue

            ts = idx.to_pydatetime().strftime("%Y-%m-%d %H:%M")

            ohlcv_list.append(
                {
                    "time": ts,
                    "open": round(float(row["Open"]), 4),
                    "high": round(float(row["High"]), 4),
                    "low": round(float(row["Low"]), 4),
                    "close": round(float(row["Close"]), 4),
                    "volume": int(row["Volume"]) if not pd.isna(row["Volume"]) else 0,
                }
            )

        if not ohlcv_list:
            return json.dumps(
                {"symbol": symbol, "error": "No valid OHLCV bars after filtering NaNs"},
                indent=2,
            )

        result: Dict[str, Any] = {
            "symbol": symbol,
            "current_price": round(float(data["Close"].iloc[-1]), 4),
            "hourly_ohlcv_last_week": ohlcv_list,
            "total_bars": len(ohlcv_list),
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps(
            {"symbol": symbol, "error": f"Failed to fetch data: {str(e)}"}, indent=2
        )

def price_ohlcv_200d_daily(symbol: str) -> str:
    """
    Returns last 200 days of *daily* OHLCV data.
    Ideal for long-range trend detection (SMA, MACD, RSI, etc.)
    """
    symbol = symbol.upper()

    try:
        ticker = yf.Ticker(symbol)

        # 1-day candles, last 200 days
        data = ticker.history(interval="1d", period="200d")

        if data.empty:
            return json.dumps(
                {"symbol": symbol, "error": "No daily data found"},
                indent=2,
            )

        ohlcv_list = []
        for idx, row in data.iterrows():
            if pd.isna(row["Open"]):
                continue

            ts = idx.strftime("%Y-%m-%d")

            ohlcv_list.append(
                {
                    "time": ts,
                    "open": round(float(row["Open"]), 4),
                    "high": round(float(row["High"]), 4),
                    "low": round(float(row["Low"]), 4),
                    "close": round(float(row["Close"]), 4),
                    "volume": int(row["Volume"]) if not pd.isna(row["Volume"]) else 0,
                }
            )

        result = {
            "symbol": symbol,
            "current_price": round(float(data["Close"].iloc[-1]), 4),
            "period": "Last 200 days (1-day bars)",
            "total_bars": len(ohlcv_list),
            "daily_ohlcv_200d": ohlcv_list,
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"symbol": symbol, "error": str(e)}, indent=2)


@tool
def trend_analysis(symbol: str, period: str = "7d") -> str:
    """
    The trend analysis functions.

    Args:
        symbol: Stock ticker
        period: "7d" or "30d" → auto-picks correct data source
    """
    symbol = symbol.upper()

    try:
        # Dynamically fetch correct data
        if period == "7d":
            raw = price_ohlcv_weekly_hourly(symbol)
            key = "hourly_ohlcv_last_week"
        elif period == "30d":
            raw = price_ohlcv_month_hourly(symbol)
            key = "hourly_ohlcv_1month"
        elif period == "200d":
            raw = price_ohlcv_200d_daily(symbol)
            key = "daily_ohlcv_200d"
        else:
            return json.dumps({"error": "period must be '7d', '30d', or '200d'"})


        data = json.loads(raw)
        if "error" in data:
            return json.dumps(data)

        bars = data.get(key, [])

        if len(bars) < 30:
            return json.dumps(
                {"symbol": symbol, "warning": "Low bar count, accuracy reduced"}
            )

        df = pd.DataFrame(bars)
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)
        close = df["close"].values
        volume = df["volume"].values

        # 1. Price Change & Direction
        pct_change = (close[-1] - close[0]) / close[0] * 100

        # 2. EMA Crossover (9 & 21)
        ema9 = pd.Series(close).ewm(span=9, adjust=False).mean().iloc[-1]
        ema21 = pd.Series(close).ewm(span=21, adjust=False).mean().iloc[-1]
        ema_trend = "bullish" if ema9 > ema21 else "bearish"

        # 3. MACD
        exp1 = pd.Series(close).ewm(span=12).mean()
        exp2 = pd.Series(close).ewm(span=26).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=9).mean()
        macd_hist = macd_line - signal_line
        macd_signal = (
            "bullish"
            if macd_line.iloc[-1] > signal_line.iloc[-1]
            and macd_hist.iloc[-1] > macd_hist.iloc[-2]
            else "bearish"
        )

        #  4. RSI (14) – Fixed & Correct
        delta = np.diff(close)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = pd.Series(gain).rolling(14).mean().iloc[-1]
        avg_loss = pd.Series(loss).rolling(14).mean().iloc[-1]
        rs = avg_gain / avg_loss if avg_loss != 0 else 100
        rsi = 100 - (100 / (1 + rs)) if rs > 0 else (0 if avg_gain == 0 else 100)

        #  5. Bollinger Bands
        sma20 = pd.Series(close).rolling(20).mean().iloc[-1]
        std20 = pd.Series(close).rolling(20).std().iloc[-1]
        upper = sma20 + 2 * std20
        lower = sma20 - 2 * std20
        bb_width = (upper - lower) / sma20
        bb_position = (close[-1] - lower) / (upper - lower) if upper != lower else 0.5
        bb_squeeze = bb_width < 0.08  # Very tight = incoming volatility

        #  6. Volume Trend
        vol_sma = pd.Series(volume).rolling(20).mean().iloc[-1]
        vol_ratio = volume[-1] / vol_sma if vol_sma > 0 else 1

        #  7. Support & Resistance (Swing Points)
        highs = df["high"].values
        lows = df["low"].values
        resistance = max(highs[-20:])
        support = min(lows[-20:])

        #  8. Trend Strength Score (0–100)
        score = 50
        score += 15 if pct_change > 3 else (-15 if pct_change < -3 else 0)
        score += 15 if ema_trend == "bullish" else -15
        score += 15 if macd_signal == "bullish" else -15
        score += 10 if rsi > 55 else (-10 if rsi < 45 else 0)
        score += 10 if close[-1] > sma20 else -10
        score += 8 if vol_ratio > 1.3 else -8
        score = max(0, min(100, score))

        #  9. Final Verdict
        if score >= 75:
            verdict = "VERY BULLISH"
            confidence = "High"
        elif score >= 60:
            verdict = "BULLISH"
            confidence = "Moderate-High"
        elif score >= 40:
            verdict = "NEUTRAL"
            confidence = "Low"
        elif score >= 25:
            verdict = "BEARISH"
            confidence = "Moderate-High"
        else:
            verdict = "VERY BEARISH"
            confidence = "High"

        result = {
            "symbol": symbol,
            "analysis_period": f"Last {period}",
            "current_price": round(close[-1], 4),
            "price_change_percent": round(pct_change, 2),
            "trend_verdict": verdict,
            "confidence": confidence,
            "trend_strength_score": int(score),
            "key_signals": {
                "ema_9_21": ema_trend.upper(),
                "macd": macd_signal.upper(),
                "rsi_14": round(rsi, 2),
                "bollinger_position": "near top"
                if bb_position > 0.8
                else "near bottom"
                if bb_position < 0.2
                else "middle",
                "bb_squeeze": "YES" if bb_squeeze else "NO",
                "volume_spike": bool(vol_ratio > 1.5),
                "near_resistance": bool(abs(close[-1] - resistance) / close[-1] < 0.01),
                "near_support": bool(abs(close[-1] - support) / close[-1] < 0.01),
            },
            "levels": {
                "resistance": round(resistance, 4),
                "support": round(support, 4),
                "sma_20": round(sma20, 4),
            },
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"symbol": symbol, "error": str(e)}, indent=2)

# if __name__ == "__main__":
#     print("7-DAYS : ")
#     print(trend_analysis("TSLA", "7d"))

#     print("\n30-DAYS : ")
#     print(trend_analysis("TSLA", "30d"))

#     print("\n 200-DAYS : ")
#     print(trend_analysis("TSLA", "200d"))
