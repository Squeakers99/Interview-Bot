import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function TimelineChart({ title, data }) {
  return (
    <section className="graph-card">
      <h2 className="graph-title">{title}</h2>
      <div className="graph-wrap">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid 
            stroke = "rgba(255,255,255,0.2)"
            strokeDasharray="3 3" 
            />
            <XAxis
              dataKey="timeSec"
              type="number"
              domain={[0, "dataMax"]}
              tickFormatter={(t) => `${t}`}
              stroke="#fff"
              tick={{ fill: "#ffffff" }}
              
            />
            <YAxis 
            domain={[0, 100]} 
            stroke="#fff"
            />
            <Tooltip />
            <Line type="monotone" dataKey="score" stroke="#000000" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
