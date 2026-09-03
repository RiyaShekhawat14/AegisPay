import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#D32F5B",
        primarySoft: "#FDF2F5",
        surface: "#FFFFFF",
        bg: "#F7F8FA",
        ink: "#17181C",
        muted: "#667085",
        border: "#E5E7EB",
        border2: "#EFF1F4",
        hover: "#F9FAFB",
        ok: "#16A34A",
        okSoft: "#F0FBF5",
        warn: "#D97706",
        warnSoft: "#FFF7ED",
        err: "#DC2626",
        errSoft: "#FEF2F2",
        info: "#2563EB",
        infoSoft: "#EFF4FF",
      },
      borderRadius: { xl2: "10px", xl3: "12px" },
    },
  },
  plugins: [],
} satisfies Config;
