from fastapi import FastAPI
import yfinance as yf

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

@app.get("/stock/{ticker}")
def get_stock(ticker: str):
    df = yf.Ticker(ticker).history(period="1y")
    return [{"date": str(d.date()), "close": round(c, 2)} for d, c in zip(df.index, df["Close"])]

import numpy as np

@app.get("/fundamentals/{ticker}")
def get_fundamentals(ticker: str):
    t = yf.Ticker(ticker)
    info = t.info
    close = t.history(period="1y")["Close"]
    daily = close.pct_change().dropna()
    return {
        "eps": info.get("trailingEps"),
        "pe": info.get("trailingPE"),
        "profit_margin": info.get("profitMargins"),
        "debt": info.get("totalDebt"),
        "free_cash_flow": info.get("freeCashflow"),
        "volatility": round(float(daily.std() * np.sqrt(252)), 4),
        "return_1y": round(float(close.iloc[-1] / close.iloc[0] - 1), 4),
    }
