// Tokyo: torii gate silhouette + Shibuya crossing grid lines
export default function TokyoLandmark() {
  return (
    <svg width="320" height="280" viewBox="0 0 320 280" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Torii gate */}
      <rect x="60" y="40" width="200" height="14" rx="7" fill="white" />
      <rect x="75" y="54" width="170" height="10" rx="5" fill="white" />
      <rect x="90" y="64" width="14" height="180" rx="7" fill="white" />
      <rect x="216" y="64" width="14" height="180" rx="7" fill="white" />
      {/* Crossing lines (Shibuya) */}
      <line x1="0" y1="260" x2="320" y2="260" stroke="white" strokeWidth="3" />
      <line x1="0" y1="270" x2="320" y2="270" stroke="white" strokeWidth="1.5" />
      <line x1="155" y1="240" x2="155" y2="280" stroke="white" strokeWidth="2" />
      <line x1="145" y1="240" x2="145" y2="280" stroke="white" strokeWidth="1" />
      <line x1="165" y1="240" x2="165" y2="280" stroke="white" strokeWidth="1" />
    </svg>
  );
}
