import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  Brain,
  FileSearch,
  MessageSquare,
  Shield,
  Sparkles,
  Upload,
} from "lucide-react";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

const features = [
  {
    icon: FileSearch,
    title: "База знаний",
    text: "Тысячи экспертных материалов: чек-листы, шпаргалки, ГОСТ 17025, ВЛК, МСИ, неопределённость.",
  },
  {
    icon: Brain,
    title: "Умный поиск",
    text: "Гибридный поиск по смыслу и ключевым словам. Готовый ответ — без вызова ИИ, быстро и точно.",
  },
  {
    icon: Sparkles,
    title: "ИИ + RAG",
    text: "Если ответа нет в базе — система ищет в ваших документах и формирует экспертный ответ со ссылками.",
  },
  {
    icon: Upload,
    title: "Ваши документы",
    text: "Загружайте PDF, DOCX, XLSX — личная база учитывается при ответах с приоритетом.",
  },
];

const steps = [
  { num: "1", title: "Задаёте вопрос", text: "По аккредитации, метрологии, пунктам ГОСТ 17025" },
  { num: "2", title: "Поиск в базе", text: "Система ищет готовый экспертный ответ и нормативные документы" },
  { num: "3", title: "Получаете ответ", text: "Из базы знаний или с помощью ИИ — с указанием источников" },
];

const examples = [
  "Требования п. 7.7 ГОСТ 17025 к ВЛК",
  "Как оформить область аккредитации?",
  "Расчёт неопределённости измерений",
  "Корректирующие действия по замечаниям эксперта",
];

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col">
      <SiteHeader variant="dark" />

      <main className="flex-1">
        {/* Hero */}
        <section className="relative overflow-hidden bg-gradient-to-br from-slate-900 via-brand-900 to-brand-700 text-white">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-brand-500/20 via-transparent to-transparent" />
          <div className="relative mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-28">
            <div className="max-w-2xl">
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-1.5 text-sm text-white/90">
                <Shield size={16} />
                ГОСТ ISO/IEC 17025-2019
              </div>
              <h1 className="text-4xl font-bold leading-tight tracking-tight sm:text-5xl">
                ИИ-эксперт по аккредитации испытательных лабораторий
              </h1>
              <p className="mt-6 text-lg text-white/80 leading-relaxed">
                Консультации по критериям аккредитации, законодательству РФ,
                требованиям Росаккредитации и метрологии — на основе вашей
                экспертной базы знаний.
              </p>
              <div className="mt-10 flex flex-wrap gap-4">
                <Link
                  href="/login"
                  className="inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3.5 text-sm font-semibold text-brand-900 transition hover:bg-brand-50"
                >
                  Войти в систему
                  <ArrowRight size={18} />
                </Link>
                <a
                  href="#как-работает"
                  className="inline-flex items-center gap-2 rounded-xl border border-white/30 px-6 py-3.5 text-sm font-medium text-white transition hover:bg-white/10"
                >
                  Как это работает
                </a>
              </div>
            </div>

            <div className="mt-16 grid grid-cols-2 gap-4 sm:grid-cols-4">
              {[
                { value: "3 000+", label: "документов" },
                { value: "20 000+", label: "фрагментов" },
                { value: "24", label: "категории" },
                { value: "≤ 2 сек", label: "готовый ответ" },
              ].map((stat) => (
                <div
                  key={stat.label}
                  className="rounded-xl border border-white/10 bg-white/5 px-4 py-4 backdrop-blur-sm"
                >
                  <div className="text-2xl font-bold">{stat.value}</div>
                  <div className="text-sm text-white/60">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features */}
        <section id="возможности" className="bg-white py-20">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <div className="text-center max-w-2xl mx-auto mb-14">
              <h2 className="text-3xl font-bold text-slate-900">Возможности</h2>
              <p className="mt-3 text-slate-600">
                Сначала база знаний, потом ИИ — экономия времени и точность ответов
              </p>
            </div>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {features.map(({ icon: Icon, title, text }) => (
                <div
                  key={title}
                  className="rounded-2xl border border-slate-200 bg-slate-50/50 p-6 transition hover:border-brand-200 hover:shadow-md"
                >
                  <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-brand-100 text-brand-600">
                    <Icon size={22} />
                  </div>
                  <h3 className="font-semibold text-slate-900">{title}</h3>
                  <p className="mt-2 text-sm text-slate-600 leading-relaxed">{text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* How it works */}
        <section id="как-работает" className="bg-slate-50 py-20">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <div className="text-center max-w-2xl mx-auto mb-14">
              <h2 className="text-3xl font-bold text-slate-900">Как это работает</h2>
            </div>
            <div className="grid gap-8 md:grid-cols-3">
              {steps.map((step) => (
                <div key={step.num} className="relative text-center">
                  <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-brand-600 text-lg font-bold text-white">
                    {step.num}
                  </div>
                  <h3 className="font-semibold text-slate-900">{step.title}</h3>
                  <p className="mt-2 text-sm text-slate-600">{step.text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Examples */}
        <section className="bg-white py-20">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <div className="rounded-2xl border border-slate-200 bg-gradient-to-br from-brand-50 to-white p-8 sm:p-12">
              <div className="flex items-start gap-4">
                <div className="hidden sm:flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white">
                  <MessageSquare size={24} />
                </div>
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-slate-900">
                    Примеры вопросов
                  </h2>
                  <p className="mt-2 text-slate-600">
                    Задайте любой из них после входа в систему
                  </p>
                  <ul className="mt-6 grid gap-3 sm:grid-cols-2">
                    {examples.map((q) => (
                      <li
                        key={q}
                        className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700"
                      >
                        <BookOpen size={16} className="shrink-0 text-brand-500" />
                        {q}
                      </li>
                    ))}
                  </ul>
                  <Link
                    href="/login"
                    className="mt-8 inline-flex items-center gap-2 rounded-xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-brand-700"
                  >
                    Задать вопрос
                    <ArrowRight size={18} />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
