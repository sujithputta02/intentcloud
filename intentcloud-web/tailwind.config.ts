import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        base: {
          light: "#F7F5F0",
          dark: "#14120E",
        },
        surface: {
          light: "#FFFFFF",
          dark: "#1C1915",
        },
        card: {
          light: "#FFFFFF",
          dark: "#221E19",
        },
        accent: {
          DEFAULT: "#B45F3C",
          hover: "#9C4F30",
          light: "#E08556",
        },
      },
      fontFamily: {
        fraunces: ["var(--font-fraunces)", "Fraunces", "Georgia", "serif"],
        inter: ["var(--font-inter)", "Inter", "-apple-system", "sans-serif"],
      },
      boxShadow: {
        card: "0 2px 14px rgba(0, 0, 0, 0.04)",
        "card-hover": "0 8px 24px rgba(0, 0, 0, 0.08)",
        hero: "0 12px 36px rgba(45, 27, 34, 0.15)",
        floating: "0 16px 40px rgba(0, 0, 0, 0.12)",
      },
      borderRadius: {
        "3xl": "24px",
        "4xl": "32px",
      },
    },
  },
  plugins: [],
};

export default config;
