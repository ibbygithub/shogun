"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/dashboard", label: "Home",     icon: "🏠" },
  { href: "/calendar",  label: "Calendar", icon: "📅" },
  { href: "/pois",      label: "Places",   icon: "📍" },
  { href: "/chat",      label: "Chat",     icon: "💬" },
  { href: "/wishlist",  label: "Wishlist", icon: "⭐" },
];

export default function MobileTabBar() {
  const pathname = usePathname();

  return (
    <nav className="mobile-tab-bar">
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
