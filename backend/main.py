import os
import requests
import numpy as np
import yfinance as yf
import anthropic
from datetime import date, datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, DateTime, JSON
from sqlalchemy.orm import declarative_base, Session
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

load_dotenv()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

analyzer = SentimentIntensityAnalyzer()
client = anthropic.Anthropic()

engine = create_engine(os.getenv("DB_URL", "postgresql+psycopg://postgres:stockpass@localhost:5432/stocks"))
Base = declarative_base()


class Cache(Base):
    __tablename__ = "cache"
    key = Column(String, primary_key=True)
    data = Column(JSON)
    created = Column(DateTime)


Base.metadata.create_all(engine)


def cached(kind, ttl_minutes):
    def deco(fn):
        @wraps(fn)
        def wrapper(ticker: str):
            key = f"{kind}:{ticker.upper()}"
            with Session(engine) as s:
                row = s.get(Cache, key)
                if row and datetime.now() - row.created < timedelta(minutes=ttl_minutes):
                    return row.data
                data = fn(ticker)
                if row:
                    row.data, row.created = data, datetime.now()
                else:
                    s.add(Cache(key=key, data=data, created=datetime.now()))
                s.commit()
                return data
        return wrapper
    return deco


@app.get("/stock/{ticker}")
@cached("stock", 15)
def get_stock(ticker: str):
    df = yf.Ticker(ticker).history(period="1y")
    return [{"date": str(d.date()), "close": round(c, 2)} for d, c in zip(df.index, df["Close"])]


@app.get("/fundamentals/{ticker}")
@cached("fund", 60)
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
@cached("news", 15)
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


@app.get("/summary/{ticker}")
@cached("summary", 60)
def get_summary(ticker: str):
    f = get_fundamentals(ticker)
    headlines = [n["title"] for n in get_news(ticker)]
    prompt = f"Write a concise 4-sentence analysis of {ticker} from these metrics and headlines. Not financial advice.\nMetrics: {f}\nHeadlines: {headlines}"
    msg = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return {"summary": msg.content[0].text}
