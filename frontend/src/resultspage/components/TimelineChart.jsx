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
  const isEye = title.toLowerCase().includes("eye");
  const lineColor = isEye ? "#0f766e" : "#1d4ed8";

  return (
    <section className="graph-card">
      <h2 className="graph-title">{title}</h2>
      <div className="graph-wrap">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid stroke="#d4deeb" strokeDasharray="3 3" />
            <XAxis
              dataKey="timeSec"
              type="number"
              domain={[0, "dataMax"]}
              tickFormatter={(t) => `${Math.round(t)}s`}
              stroke="#5f708a"
              tick={{ fill: "#4d5f7b", fontSize: 12 }}
            />
            <YAxis
              domain={[0, 100]}
              stroke="#5f708a"
              tick={{ fill: "#4d5f7b", fontSize: 12 }}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip
              formatter={(value) => [`${Math.round(value)}%`, "Score"]}
              labelFormatter={(value) => `Time: ${Number(value).toFixed(2)}s`}
              contentStyle={{
                borderRadius: "10px",
                border: "1px solid #ccd7e5",
                background: "#f8fbff",
              }}
            />
            <Line type="monotone" dataKey="score" stroke={lineColor} strokeWidth={3} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
