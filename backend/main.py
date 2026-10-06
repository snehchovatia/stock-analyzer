from fastapi import FastAPI
import yfinance as yf

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

@app.get("/stock/{ticker}")
def get_stock(ticker: str):
    df = yf.Ticker(ticker).history(period="1y")
    return [{"date": str(d.date()), "close": round(c, 2)} for d, c in zip(df.index, df["Close"])]
