import { Shield } from "lucide-react";

export function SiteFooter() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 py-8 sm:flex-row sm:px-6">
        <div className="flex items-center gap-2 text-slate-600">
          <Shield size={18} className="text-brand-600" />
          <span className="text-sm font-medium text-slate-800">Expert17025</span>
          <span className="text-sm text-slate-400">© {new Date().getFullYear()}</span>
        </div>
        <p className="text-center text-xs text-slate-500 sm:text-right">
          ГОСТ ISO/IEC 17025-2019 · Росаккредитация · Метрология
        </p>
      </div>
    </footer>
  );
}
