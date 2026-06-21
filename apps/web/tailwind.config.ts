import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./features/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        court: {
          DEFAULT: "#d97706",
          dark: "#b45309",
        },
      },
    },
  },
  plugins: [],
};

export default config;
