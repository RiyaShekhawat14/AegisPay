import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#D32F5B",
        surface: "#FFFFFF",
        bg: "#F7F8FA",
        ink: "#17181C",
        muted: "#667085",
        border: "#E5E7EB",
        hover: "#F9FAFB",
        ok: "#16A34A",
        warn: "#D97706",
        err: "#DC2626",
      },
    },
  },
  plugins: [],
} satisfies Config;
