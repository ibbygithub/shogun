"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/dashboard", label: "Home",      icon: "🏠" },
  { href: "/calendar",  label: "Calendar",  icon: "📅" },
  { href: "/planning",  label: "Planning",  icon: "📋" },
  { href: "/pois",      label: "Places",    icon: "📍" },
  { href: "/phrases",   label: "Phrases",   icon: "🗣️" },
  { href: "/checklist", label: "Checklist", icon: "✅" },
  { href: "/budget",    label: "Budget",    icon: "💴" },
  { href: "/chat",      label: "Chat",      icon: "💬" },
];

export default function MobileTabBar() {
  const pathname = usePathname();

  return (
    <nav className="mobile-tab-bar" style={{ overflowX: "auto" }}>
      {TABS.map((tab) => {
        const active = pathname === tab.href || pathname.startsWith(tab.href + "/");
        return (
          <Link key={tab.href} href={tab.href}
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "2px",
              color: active ? "white" : "rgba(255,255,255,0.5)",
              textDecoration: "none",
              fontSize: "0.6rem",
              padding: "4px 8px",
              flexShrink: 0,
            }}
          >
            <span style={{ fontSize: "1.25rem" }}>{tab.icon}</span>
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
