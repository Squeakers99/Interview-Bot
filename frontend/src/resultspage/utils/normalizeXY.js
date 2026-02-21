export function normalizeXY(arr) {
  return (arr || [])
    .map((p, i) => {
      const isPair = Array.isArray(p);
      let timeSec = Number(isPair ? p[0] : p?.x ?? p?.timestamp ?? i);
      let score = Number(isPair ? p[1] : p?.y ?? p?.score ?? p?.percentage ?? 0);

      if (Number.isFinite(timeSec) && timeSec > 1000) timeSec = timeSec / 1000;
      if (Number.isFinite(score) && score <= 1) score = score * 100;

      score = Math.max(0, Math.min(100, score));

      return { timeSec, score };
    })
    .sort((a, b) => a.timeSec - b.timeSec);
}
