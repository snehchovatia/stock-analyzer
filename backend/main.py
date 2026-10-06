import os
import requests
from datetime import date, timedelta
from dotenv import load_dotenv
import numpy as np
import yfinance as yf
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

load_dotenv()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

analyzer = SentimentIntensityAnalyzer()


@app.get("/stock/{ticker}")
def get_stock(ticker: str):
    df = yf.Ticker(ticker).history(period="1y")
    return [{"date": str(d.date()), "close": round(c, 2)} for d, c in zip(df.index, df["Close"])]


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


@app.get("/news/{ticker}")
def get_news(ticker: str):
    today = date.today()
    r = requests.get("https://finnhub.io/api/v1/company-news", params={
        "symbol": ticker,
        "from": str(today - timedelta(days=7)),
        "to": str(today),
        "token": os.getenv("FINNHUB_KEY"),
    })
    return [
        {"title": n["headline"], "url": n["url"], "score": analyzer.polarity_scores(n["headline"])["compound"]}
        for n in r.json()[:10]
    ]
