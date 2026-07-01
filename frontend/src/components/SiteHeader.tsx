import Link from "next/link";
import { Shield } from "lucide-react";

interface Props {
  variant?: "light" | "dark";
}

export function SiteHeader({ variant = "light" }: Props) {
  const isDark = variant === "dark";

  return (
    <header
      className={`sticky top-0 z-50 border-b backdrop-blur-md ${
        isDark
          ? "border-white/10 bg-slate-900/80 text-white"
          : "border-slate-200/80 bg-white/90 text-slate-900"
      }`}
    >
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2.5">
          <div
            className={`flex h-9 w-9 items-center justify-center rounded-lg ${
              isDark ? "bg-brand-500" : "bg-brand-600"
            }`}
          >
            <Shield className="text-white" size={20} />
          </div>
          <div>
            <span className="font-bold tracking-tight">Expert17025</span>
            <span
              className={`ml-2 hidden text-xs sm:inline ${
                isDark ? "text-white/60" : "text-slate-500"
              }`}
            >
              Аккредитация лабораторий
            </span>
          </div>
        </Link>

        <nav className="flex items-center gap-2 sm:gap-4">
          <a
            href="#возможности"
            className={`hidden text-sm sm:inline ${
              isDark ? "text-white/70 hover:text-white" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Возможности
          </a>
          <a
            href="#как-работает"
            className={`hidden text-sm sm:inline ${
              isDark ? "text-white/70 hover:text-white" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Как работает
          </a>
          <Link
            href="/login"
            className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
              isDark
                ? "text-white/90 hover:bg-white/10"
                : "text-slate-700 hover:bg-slate-100"
            }`}
          >
            Войти
          </Link>
          <Link
            href="/login"
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-700"
          >
            Начать
          </Link>
        </nav>
      </div>
    </header>
  );
}
