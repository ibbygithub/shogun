import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Shogun — Japan Trip",
  description: "AI travel concierge for the Ibbotson Japan trip 2026",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
