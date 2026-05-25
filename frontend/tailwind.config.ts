import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        primary: "#b7122a",
        "on-primary": "#ffffff",
        "primary-container": "#db313f",
        secondary: "#4648d4",
        "secondary-container": "#6063ee",
        tertiary: "#006762",
        "tertiary-container": "#00837c",
        background: "#fcf9f8",
        surface: "#fcf9f8",
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#f6f3f2",
        "surface-container": "#f0eded",
        "surface-container-high": "#eae7e7",
        "surface-dim": "#dcd9d9",
        "on-surface": "#1b1b1b",
        "on-surface-variant": "#5b403f",
        "on-background": "#1b1b1b",
        outline: "#8f6f6e",
        "outline-variant": "#e4bebc",
        error: "#ba1a1a",
        "error-container": "#ffdad6",
        "on-error-container": "#93000a",
      },
      fontFamily: {
        display: ["var(--font-dm-sans)", "DM Sans", "sans-serif"],
        body: ["var(--font-inter)", "Inter", "sans-serif"],
      },
      borderRadius: {
        xl: "0.75rem",
        "2xl": "1rem",
      },
      spacing: {
        "margin-mobile": "16px",
        "margin-desktop": "48px",
        gutter: "24px",
      },
      maxWidth: {
        content: "1280px",
      },
      boxShadow: {
        card: "0px 4px 12px rgba(0, 0, 0, 0.05)",
        "card-hover": "0px 8px 24px rgba(0, 0, 0, 0.1)",
        footer: "0px -4px 16px rgba(0, 0, 0, 0.08)",
      },
      animation: {
        shimmer: "shimmer 3s infinite linear",
        float: "float 3s ease-in-out infinite",
        pulsering: "pulsering 1.25s ease-out infinite",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "200% 0" },
          "100%": { backgroundPosition: "-200% 0" },
        },
        float: {
          "0%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
          "100%": { transform: "translateY(0)" },
        },
        pulsering: {
          "0%": { transform: "scale(0.5)", opacity: "0.8" },
          "100%": { transform: "scale(1.4)", opacity: "0" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
