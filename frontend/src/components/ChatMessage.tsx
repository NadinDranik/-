"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, Check, Database, Sparkles } from "lucide-react";
import { useState } from "react";
import type { Message } from "@/lib/api";

interface Props {
  message: Message;
}

export function ChatMessage({ message }: Props) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";

  const copy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-brand-600 text-white"
            : "bg-white border border-slate-200 shadow-sm"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <>
            <div className="prose-chat text-sm">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            </div>
            <div className="mt-3 flex items-center gap-3 text-xs text-slate-500 border-t border-slate-100 pt-2">
              {message.source === "knowledge_base" ? (
                <span className="flex items-center gap-1 text-emerald-600">
                  <Database size={14} /> Из базы знаний
                </span>
              ) : (
                <span className="flex items-center gap-1 text-blue-600">
                  <Sparkles size={14} /> ИИ + RAG
                </span>
              )}
              {message.response_time_ms && <span>{message.response_time_ms} мс</span>}
              {message.tokens_used != null && message.tokens_used > 0 && (
                <span>{message.tokens_used} токенов</span>
              )}
              <button
                onClick={copy}
                className="ml-auto flex items-center gap-1 hover:text-slate-700"
              >
                {copied ? <Check size={14} /> : <Copy size={14} />}
                {copied ? "Скопировано" : "Копировать"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
