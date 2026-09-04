import type { Config } from "tailwindcss";

// Colors are sourced from src/styles/tokens.css (single source of truth).
const colors = {
  primary: "var(--brand)",
  primarySoft: "var(--brand-soft)",
  surface: "var(--surface)",
  bg: "var(--background)",
  ink: "var(--text)",
  muted: "var(--text-muted)",
  border: "var(--border)",
  border2: "var(--border-muted)",
  hover: "var(--surface-muted)",
  ok: "var(--success)",
  okSoft: "var(--success-soft)",
  warn: "var(--warning)",
  warnSoft: "var(--warning-soft)",
  err: "var(--danger)",
  errSoft: "var(--danger-soft)",
  info: "var(--info)",
  infoSoft: "var(--info-soft)",
};

export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors,
      borderRadius: { xl2: "10px", xl3: "12px" },
      fontFamily: { sans: ["var(--font-sans)"] },
      boxShadow: {
        card: "var(--shadow-card)",
        pop: "var(--shadow-pop)",
      },
    },
  },
  plugins: [],
} satisfies Config;
