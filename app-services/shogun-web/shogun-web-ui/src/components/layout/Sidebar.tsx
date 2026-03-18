"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { CITIES } from "@/lib/cities";

const MAIN_NAV = [
  { href: "/dashboard",  label: "Dashboard",   icon: "🏠" },
  { href: "/calendar",   label: "Calendar",    icon: "📅" },
  { href: "/planning",   label: "Planning",    icon: "📋" },
  { href: "/itinerary",  label: "Itinerary",   icon: "🗺️" },
  { href: "/pois",       label: "Places",      icon: "📍" },
  { href: "/chat",       label: "Chat Shogun", icon: "💬" },
  { href: "/wishlist",   label: "Wishlist",    icon: "⭐" },
];

const TOOLS_NAV = [
  { href: "/phrases",   label: "Phrases",   icon: "🗣️" },
  { href: "/transit",   label: "Transit",   icon: "🚆" },
  { href: "/checklist", label: "Checklist", icon: "✅" },
  { href: "/budget",    label: "Budget",    icon: "💴" },
];

const ADMIN_NAV = [
  { href: "/settings", label: "Settings", icon: "⚙️" },
  { href: "/admin",    label: "Admin",    icon: "🔧" },
];

function NavLink({ href, label, icon, pathname }: { href: string; label: string; icon: string; pathname: string }) {
  const active = pathname === href || pathname.startsWith(href + "/");
  return (
    <Link href={href}
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
      <span>{icon}</span>
      {label}
    </Link>
  );
}

function SectionLabel({ label }: { label: string }) {
  return (
    <div style={{
      padding: "0.6rem 1rem 0.25rem",
      fontSize: "0.65rem",
      color: "rgba(255,255,255,0.35)",
      textTransform: "uppercase",
      letterSpacing: "0.08em",
      marginTop: "0.25rem",
    }}>
      {label}
    </div>
  );
}

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
      <div style={{ padding: "0.75rem 0", flex: 1, overflowY: "auto" }}>
        {MAIN_NAV.map((item) => (
          <NavLink key={item.href} {...item} pathname={pathname} />
        ))}

        {/* Trip tools section */}
        <div style={{ borderTop: "1px solid rgba(255,255,255,0.08)", marginTop: "0.5rem" }}>
          <SectionLabel label="Trip Tools" />
          {TOOLS_NAV.map((item) => (
            <NavLink key={item.href} {...item} pathname={pathname} />
          ))}
        </div>

        {/* Admin section */}
        <div style={{ borderTop: "1px solid rgba(255,255,255,0.08)", marginTop: "0.5rem" }}>
          {ADMIN_NAV.map((item) => (
            <NavLink key={item.href} {...item} pathname={pathname} />
          ))}
        </div>
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
