import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

type Point = { date: string; close: number };

export default function App() {
  const [ticker, setTicker] = useState("NVDA");
  const [data, setData] = useState<Point[]>([]);

  const load = async () => {
    const res = await fetch(`http://127.0.0.1:8000/stock/${ticker}`);
    setData(await res.json());
  };

  return (
    <div style={{ padding: 24 }}>
      <h1>Stock Analyzer</h1>
      <input value={ticker} onChange={(e) => setTicker(e.target.value.toUpperCase())} />
      <button onClick={load}>Analyze</button>
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
    </div>
  );
}