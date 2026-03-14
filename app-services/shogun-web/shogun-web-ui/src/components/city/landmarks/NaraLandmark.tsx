// Nara: Todaiji Nandaimon gate outline + deer silhouette
export default function NaraLandmark() {
  return (
    <svg width="320" height="280" viewBox="0 0 320 280" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Gate columns */}
      <rect x="40" y="80" width="18" height="180" rx="4" fill="white" />
      <rect x="262" y="80" width="18" height="180" rx="4" fill="white" />
      <rect x="100" y="100" width="14" height="160" rx="4" fill="white" />
      <rect x="206" y="100" width="14" height="160" rx="4" fill="white" />
      {/* Roof tiers */}
      <path d="M20 80 L160 40 L300 80 Z" fill="white" />
      <path d="M50 100 L160 68 L270 100 Z" fill="white" />
      {/* Deer silhouette */}
      <ellipse cx="195" cy="220" rx="28" ry="20" fill="white" />
      <rect x="187" y="200" width="10" height="28" rx="5" fill="white" />
      <circle cx="192" cy="196" r="12" fill="white" />
      {/* Antlers */}
      <path d="M190 184 L184 170 M184 170 L178 162 M184 170 L188 163" stroke="white" strokeWidth="3" strokeLinecap="round" />
      <path d="M194 184 L200 170 M200 170 L206 162 M200 170 L196 163" stroke="white" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}
