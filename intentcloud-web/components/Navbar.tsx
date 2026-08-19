"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

export default function Navbar() {
  const [theme, setTheme] = useState<"light" | "dark" | "system">("system");
  const [mounted, setMounted] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    setMounted(true);
    const stored = (localStorage.getItem("theme") || "system") as "light" | "dark" | "system";
    setTheme(stored);
  }, []);

  const toggleTheme = (newTheme: "light" | "dark" | "system") => {
    setTheme(newTheme);
    localStorage.setItem("theme", newTheme);

    const isDark =
      newTheme === "dark" ||
      (newTheme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
    document.documentElement.classList.toggle("dark", isDark);
  };

  if (!mounted) return null;

  return (
    <header className="sticky top-0 z-40 w-full bg-[var(--bg-base)]/80 backdrop-blur-md border-b border-[var(--border-subtle)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link
          href="/"
          className="font-fraunces text-2xl font-bold text-[var(--text-primary)] tracking-tight hover:opacity-90 transition flex items-center gap-2"
        >
          <span className="w-8 h-8 rounded-xl bg-[var(--accent)] text-white flex items-center justify-center text-sm font-bold shadow-sm">
            IC
          </span>
          <span>IntentCloud</span>
        </Link>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-2">
          <Link
            href="/"
            className={`px-4 py-2 rounded-full text-sm font-medium transition ${
              pathname === "/"
                ? "bg-[var(--text-primary)] text-[var(--bg-surface)] font-semibold shadow-sm"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)]"
            }`}
          >
            Dashboard
          </Link>
          <Link
            href="/search"
            className={`px-4 py-2 rounded-full text-sm font-medium transition ${
              pathname === "/search"
                ? "bg-[var(--text-primary)] text-[var(--bg-surface)] font-semibold shadow-sm"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)]"
            }`}
          >
            Intent Search
          </Link>
          <Link
            href="/upload"
            className={`px-4 py-2 rounded-full text-sm font-medium transition ${
              pathname === "/upload"
                ? "bg-[var(--text-primary)] text-[var(--bg-surface)] font-semibold shadow-sm"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)]"
            }`}
          >
            Upload
          </Link>
        </nav>

        {/* Theme Toggle & Avatar */}
        <div className="flex items-center gap-3">
          {/* Light/Dark/System Toggle */}
          <div className="flex items-center p-1 rounded-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-xs shadow-sm">
            {(["light", "dark", "system"] as const).map((t) => (
              <button
                key={t}
                onClick={() => toggleTheme(t)}
                type="button"
                className={`px-2.5 py-1 rounded-full transition capitalize font-medium ${
                  theme === t
                    ? "bg-[var(--accent)] text-white font-semibold shadow-sm"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          {/* Profile Avatar */}
          <div className="w-10 h-10 rounded-full bg-[var(--accent)] text-white font-fraunces font-bold text-sm flex items-center justify-center shadow-sm select-none">
            R
          </div>
        </div>
      </div>
    </header>
  );
}
