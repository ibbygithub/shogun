// Osaka: Dotonbori neon sign shapes
export default function OsakaLandmark() {
  return (
    <svg width="320" height="280" viewBox="0 0 320 280" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Large sign frame */}
      <rect x="40" y="40" width="240" height="160" rx="8" stroke="white" strokeWidth="4" fill="none" />
      {/* Inner text blocks (stylized kanji shapes) */}
      <rect x="64" y="70" width="40" height="40" rx="4" fill="white" />
      <rect x="120" y="70" width="40" height="40" rx="4" fill="white" />
      <rect x="176" y="70" width="40" height="40" rx="4" fill="white" />
      <rect x="232" y="70" width="24" height="40" rx="4" fill="white" />
      {/* Glico running man simplified */}
      <circle cx="270" cy="160" r="14" fill="white" />
      <rect x="263" y="174" width="14" height="36" rx="7" fill="white" />
      <line x1="250" y1="190" x2="263" y2="185" stroke="white" strokeWidth="5" strokeLinecap="round" />
      <line x1="290" y1="188" x2="277" y2="185" stroke="white" strokeWidth="5" strokeLinecap="round" />
      {/* Reflection */}
      <line x1="40" y1="215" x2="280" y2="215" stroke="white" strokeWidth="2" opacity="0.5" />
      <rect x="40" y="222" width="240" height="6" rx="3" fill="white" opacity="0.15" />
    </svg>
  );
}
