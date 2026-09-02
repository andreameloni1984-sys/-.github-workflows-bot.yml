import json
import os
import time
from datetime import datetime, timezone

import requests


# ============================================================
# CONFIGURAZIONE
# ============================================================

SYMBOL = "XAUUSD"

# Numero di candele richieste
CANDLES = 200

# Intervallo dati: 15 minuti
INTERVAL = "15min"

# Soglia minima per generare un segnale
MIN_SCORE = 3


# ============================================================
# FUNZIONI
# ============================================================

def get_gold_price():
    """
    Recupera il prezzo dell'oro.
    Utilizza l'API di Twelve Data.

    È necessario creare una API key gratuita e inserirla
    nei Secrets di GitHub come TWELVE_DATA_API_KEY.
    """

    api_key = os.getenv("TWELVE_DATA_API_KEY")

    if not api_key:
        raise RuntimeError(
            "TWELVE_DATA_API_KEY non configurata nei GitHub Secrets."
        )

    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "outputsize": CANDLES,
        "apikey": api_key,
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()

    if "values" not in data:
        raise RuntimeError(f"Errore API: {data}")

    candles = data["values"]

    candles.reverse()

    return candles


def sma(values, period):
    """Simple Moving Average."""

    if len(values) < period:
        return None

    return sum(values[-period:]) / period


def ema(values, period):
    """Exponential Moving Average."""

    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)

    result = sum(values[:period]) / period

    for price in values[period:]:
        result = (price - result) * multiplier + result

    return result


def calculate_rsi(values, period=14):
    """Calcola RSI."""

    if len(values) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(1, len(values)):
        change = values[i] - values[i - 1]

        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


def calculate_signal(candles):
    """Genera il segnale BUY / SELL / WAIT."""

    closes = [float(c["close"]) for c in candles]

    price = closes[-1]

    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)

    sma200 = sma(closes, 200)

    rsi = calculate_rsi(closes, 14)

    buy_score = 0
    sell_score = 0

    # --------------------------------------------------------
    # TREND
    # --------------------------------------------------------

    if ema20 and ema50:

        if ema20 > ema50:
            buy_score += 1

        elif ema20 < ema50:
            sell_score += 1

    # --------------------------------------------------------
    # PREZZO VS EMA 20
    # --------------------------------------------------------

    if ema20:

        if price > ema20:
            buy_score += 1

        elif price < ema20:
            sell_score += 1

    # --------------------------------------------------------
    # PREZZO VS SMA 200
    # --------------------------------------------------------

    if sma200:

        if price > sma200:
            buy_score += 1

        elif price < sma200:
            sell_score += 1

    # --------------------------------------------------------
    # RSI
    # --------------------------------------------------------

    if rsi is not None:

        if 50 < rsi < 70:
            buy_score += 1

        elif 30 < rsi < 50:
            sell_score += 1

    # --------------------------------------------------------
    # DECISIONE
    # --------------------------------------------------------

    if buy_score >= MIN_SCORE and buy_score > sell_score:
        signal = "BUY"

    elif sell_score >= MIN_SCORE and sell_score > buy_score:
        signal = "SELL"

    else:
        signal = "WAIT"

    return {
        "signal": signal,
        "price": round(price, 2),
        "ema20": round(ema20, 2) if ema20 else None,
        "ema50": round(ema50, 2) if ema50 else None,
        "sma200": round(sma200, 2) if sma200 else None,
        "rsi": round(rsi, 2) if rsi else None,
        "buy_score": buy_score,
        "sell_score": sell_score,
        "time": candles[-1]["datetime"],
    }


def save_result(result):
    """Salva l'ultimo segnale in un file JSON."""

    with open("signal.json", "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("GOLD TRADING BOT")
    print("=" * 60)

    print(f"Strumento: {SYMBOL}")
    print(f"Timeframe: {INTERVAL}")
    print()

    try:

        candles = get_gold_price()

        result = calculate_signal(candles)

        save_result(result)

        print(f"Prezzo:     {result['price']}")
        print(f"EMA 20:     {result['ema20']}")
        print(f"EMA 50:     {result['ema50']}")
        print(f"SMA 200:    {result['sma200']}")
        print(f"RSI:        {result['rsi']}")
        print()
        print(f"BUY score:  {result['buy_score']}")
        print(f"SELL score: {result['sell_score']}")
        print()
        print(f"SEGNale:    {result['signal']}")
        print(f"Ora:        {result['time']}")
        print("=" * 60)

    except Exception as error:

        print("ERRORE:")
        print(error)

        raise


if __name__ == "__main__":
    main()