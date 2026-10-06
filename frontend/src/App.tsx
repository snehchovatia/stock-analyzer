import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

type Point = { date: string; close: number };
type Fund = { eps: number; pe: number; profit_margin: number; debt: number; free_cash_flow: number; volatility: number; return_1y: number };
type News = { title: string; url: string; score: number };

export default function App() {
  const [ticker, setTicker] = useState("NVDA");
  const [data, setData] = useState<Point[]>([]);
  const [fund, setFund] = useState<Fund | null>(null);
  const [news, setNews] = useState<News[]>([]);

  const load = async () => {
    const [p, f, n] = await Promise.all([
      fetch(`http://127.0.0.1:8000/stock/${ticker}`).then((r) => r.json()),
      fetch(`http://127.0.0.1:8000/fundamentals/${ticker}`).then((r) => r.json()),
      fetch(`http://127.0.0.1:8000/news/${ticker}`).then((r) => r.json()),
    ]);
    setData(p);
    setFund(f);
    setNews(n);
  };

  return (
    <div style={{ padding: 24 }}>
      <h1>Stock Analyzer</h1>
      <input value={ticker} onChange={(e) => setTicker(e.target.value.toUpperCase())} />
      <button onClick={load}>Analyze</button>
      {fund && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12, marginTop: 24 }}>
          {[
            ["EPS", fund.eps?.toFixed(2)],
            ["P/E", fund.pe?.toFixed(1)],
            ["Profit margin", `${(fund.profit_margin * 100).toFixed(1)}%`],
            ["Debt", `$${(fund.debt / 1e9).toFixed(1)}B`],
            ["Free cash flow", `$${(fund.free_cash_flow / 1e9).toFixed(1)}B`],
            ["Volatility", `${(fund.volatility * 100).toFixed(1)}%`],
            ["1Y return", `${(fund.return_1y * 100).toFixed(1)}%`],
          ].map(([label, value]) => (
            <div key={label} style={{ border: "1px solid #444", borderRadius: 8, padding: 12 }}>
              <div style={{ opacity: 0.6, fontSize: 13 }}>{label}</div>
              <div style={{ fontSize: 22 }}>{value}</div>
            </div>
          ))}
        </div>
      )}
      <div style={{ width: "100%", height: 400, marginTop: 24 }}>
        <ResponsiveContainer>
          <LineChart data={data}>
            <XAxis dataKey="date" minTickGap={40} />
            <YAxis domain={["auto", "auto"]} />
            <Tooltip />
            <Line type="monotone" dataKey="close" dot={false} stroke="#76b900" />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <h2 style={{ marginTop: 24 }}>News sentiment</h2>
      {news.map((n) => (
        <div key={n.url} style={{ padding: "8px 0", borderBottom: "1px solid #333" }}>
          <span style={{ color: n.score > 0.05 ? "#76b900" : n.score < -0.05 ? "#e5484d" : "#999", marginRight: 8 }}>
            {n.score.toFixed(2)}
          </span>
          {n.title}
        </div>
      ))}
    </div>
  );
}