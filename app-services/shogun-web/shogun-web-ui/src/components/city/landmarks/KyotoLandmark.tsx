// Kyoto: Fushimi Inari torii tunnel perspective (repeating, diminishing)
export default function KyotoLandmark() {
  const gates = [
    { x: 20, width: 280, barH: 18, colW: 20, y: 30 },
    { x: 50, width: 220, barH: 14, colW: 16, y: 80 },
    { x: 80, width: 160, barH: 11, colW: 13, y: 120 },
    { x: 105, width: 110, barH: 8, colW: 10, y: 152 },
    { x: 122, width: 76, barH: 6, colW: 8, y: 177 },
    { x: 136, width: 48, barH: 5, colW: 6, y: 196 },
  ];

  return (
    <svg width="320" height="280" viewBox="0 0 320 280" fill="none" xmlns="http://www.w3.org/2000/svg">
      {gates.map((g, i) => (
        <g key={i} opacity={1 - i * 0.12}>
          {/* Top bar */}
          <rect x={g.x} y={g.y} width={g.width} height={g.barH} rx={g.barH / 2} fill="white" />
          {/* Sub-bar */}
          <rect x={g.x + g.colW} y={g.y + g.barH} width={g.width - g.colW * 2} height={Math.round(g.barH * 0.6)} rx={2} fill="white" />
          {/* Left column */}
          <rect x={g.x + g.colW} y={g.y + g.barH} width={g.colW} height={280 - g.y - g.barH} rx={g.colW / 2} fill="white" />
          {/* Right column */}
          <rect x={g.x + g.width - g.colW * 2} y={g.y + g.barH} width={g.colW} height={280 - g.y - g.barH} rx={g.colW / 2} fill="white" />
        </g>
      ))}
    </svg>
  );
}
