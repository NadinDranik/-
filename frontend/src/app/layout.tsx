import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Expert17025 — ИИ-эксперт по аккредитации",
  description: "Экспертная система по ГОСТ ISO/IEC 17025 и аккредитации испытательных лабораторий",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
