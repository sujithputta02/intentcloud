import type { Metadata } from "next";
import { Inter, Fraunces } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import ThemeProvider from "@/components/ThemeProvider";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  display: "swap",
});

export const metadata: Metadata = {
  title: "IntentCloud - Intent-Aware Cognitive Memory",
  description: "Search your files using natural language with AI-powered intent understanding",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                const stored = localStorage.getItem('theme') || 'system';
                const isDark = stored === 'dark' ||
                  (stored === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
                document.documentElement.classList.toggle('dark', isDark);
              })();
            `,
          }}
        />
      </head>
      <body className={`${inter.variable} ${fraunces.variable} antialiased`}>
        <ThemeProvider>
          <Navbar />
          <main className="min-h-screen bg-[var(--bg-base)]">
            {children}
          </main>
        </ThemeProvider>
      </body>
    </html>
  );
}
