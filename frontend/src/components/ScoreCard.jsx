export default function ScoreCard({ title, score, goodPct, hint }) {
  return (
    <div style={panel}>
      <h2 style={{ marginTop: 0, marginBottom: 8 }}>{title}</h2>

      <div style={{ display: "flex", gap: 12, alignItems: "baseline" }}>
        <div style={{ fontSize: 46, fontWeight: 800 }}>{score ?? "--"}</div>
        <div style={{ color: "#555" }}>/ 100</div>
      </div>

      <div style={{ marginTop: 8, color: "#444" }}>
        <b>Good-time:</b> {goodPct}% of session
      </div>

      <div style={{ marginTop: 8, color: "#666" }}>{hint}</div>
    </div>
  );
}

const panel = {
  padding: 14,
  border: "1px solid #ddd",
  borderRadius: 12,
  background: "#fff",
  marginBottom: 14,
};