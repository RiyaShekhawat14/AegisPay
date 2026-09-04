import type { Metadata } from "next";
import "./globals.css";
import "../styles/tokens.css";
import "../styles/components.css";

export const metadata: Metadata = {
  title: "AegisPay — Merchant & AI Buyer",
  description: "The Trust & Growth Layer for Agentic Commerce",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-bg text-ink antialiased">{children}</body>
    </html>
  );
}
