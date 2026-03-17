import Link from "next/link";

export default function LandingPage() {
  return (
    <div
      style={{
        position: "relative",
        width: "100vw",
        height: "100vh",
        overflow: "hidden",
        background: "#0d0a06",
      }}
    >
      {/* Hero image — full bleed, shifted up to reveal bottom-left logo */}
      <img
        src="/shogun-landing.png"
        alt="Shogun Concierge"
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          objectFit: "cover",
          objectPosition: "center 35%",
        }}
      />

      {/* Enter button — top center */}
      <div
        style={{
          position: "absolute",
          top: "2rem",
          left: "50%",
          transform: "translateX(-50%)",
        }}
      >
        <Link
          href="/dashboard"
          style={{
            display: "inline-block",
            padding: "1rem 3rem",
            background: "rgba(0,0,0,0.72)",
            color: "#fff",
            borderRadius: "999px",
            fontSize: "1.1rem",
            fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            fontWeight: 500,
            letterSpacing: "0.04em",
            textDecoration: "none",
            border: "1.5px solid rgba(255,255,255,0.55)",
            backdropFilter: "blur(6px)",
            boxShadow: "0 4px 24px rgba(0,0,0,0.45)",
            whiteSpace: "nowrap",
          }}
        >
          Enter →
        </Link>
      </div>
    </div>
  );
}
