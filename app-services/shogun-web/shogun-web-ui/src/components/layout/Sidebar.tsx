"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { CITIES } from "@/lib/cities";

const NAV = [
  { href: "/dashboard",  label: "Dashboard",  icon: "🏠" },
  { href: "/calendar",   label: "Calendar",   icon: "📅" },
  { href: "/itinerary",  label: "Itinerary",  icon: "🗺️" },
  { href: "/pois",       label: "Places",     icon: "📍" },
  { href: "/chat",       label: "Chat Shogun", icon: "💬" },
  { href: "/wishlist",   label: "Wishlist",   icon: "⭐" },
  { href: "/settings",   label: "Settings",   icon: "⚙️" },
  { href: "/admin",      label: "Admin",      icon: "🔧" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className="sidebar">
      {/* Logo */}
      <div style={{ padding: "1.5rem 1rem 1rem", borderBottom: "1px solid rgba(255,255,255,0.1)" }}>
        <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "white", letterSpacing: "-0.02em" }}>
          将軍
        </div>
        <div style={{ fontSize: "0.75rem", color: "rgba(255,255,255,0.5)", marginTop: "0.25rem" }}>
          Japan · Mar–Apr 2026
        </div>
      </div>

      {/* Main nav */}
      <div style={{ padding: "0.75rem 0", flex: 1 }}>
        {NAV.map((item) => {
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link key={item.href} href={item.href}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.625rem",
                padding: "0.625rem 1rem",
                color: active ? "white" : "rgba(255,255,255,0.65)",
                background: active ? "rgba(255,255,255,0.12)" : "transparent",
                textDecoration: "none",
                fontSize: "0.875rem",
                fontWeight: active ? 600 : 400,
                borderRight: active ? "3px solid var(--city-highlight)" : "3px solid transparent",
                transition: "all 0.15s",
              }}
            >
              <span>{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </div>

      {/* City quick links */}
      <div style={{ padding: "0.75rem 0", borderTop: "1px solid rgba(255,255,255,0.1)" }}>
        <div style={{ padding: "0.25rem 1rem 0.5rem", fontSize: "0.7rem", color: "rgba(255,255,255,0.4)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
          Cities
        </div>
        {Object.values(CITIES).map((city) => (
          <Link key={city.slug} href={`/city/${city.slug}`}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "0.4rem 1rem",
              color: "rgba(255,255,255,0.7)",
              textDecoration: "none",
              fontSize: "0.8rem",
              transition: "color 0.15s",
            }}
          >
            <span>{city.name}</span>
            <span style={{ fontSize: "0.7rem", color: "rgba(255,255,255,0.4)" }}>{city.kanji}</span>
          </Link>
        ))}
      </div>
    </nav>
  );
}
