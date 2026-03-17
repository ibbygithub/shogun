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
      {/* Hero image — full bleed */}
      <img
        src="/shogun-landing.png"
        alt="Shogun Concierge"
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          objectFit: "cover",
          objectPosition: "center",
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
            padding: "0.6rem 1.8rem",
            background: "rgba(0,0,0,0.55)",
            color: "#fff",
            borderRadius: "999px",
            fontSize: "0.95rem",
            fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            fontWeight: 500,
            letterSpacing: "0.04em",
            textDecoration: "none",
            border: "1px solid rgba(255,255,255,0.25)",
            backdropFilter: "blur(6px)",
            whiteSpace: "nowrap",
          }}
        >
          Enter →
        </Link>
      </div>

      {/* Login link — bottom right */}
      <div
        style={{
          position: "absolute",
          bottom: "1.5rem",
          right: "1.75rem",
        }}
      >
        <Link
          href="/dashboard"
          style={{
            color: "rgba(255,255,255,0.75)",
            fontSize: "0.8rem",
            fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            textDecoration: "none",
            letterSpacing: "0.03em",
          }}
        >
          Login →
        </Link>
      </div>
    </div>
  );
}
