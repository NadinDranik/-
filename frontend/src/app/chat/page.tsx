"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Plus,
  Send,
  LogOut,
  MessageSquare,
  Upload,
  Loader2,
  Shield,
} from "lucide-react";
import { api, type Chat, type Message, type User } from "@/lib/api";
import { ChatMessage } from "@/components/ChatMessage";

export default function ChatPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChat, setActiveChat] = useState<Chat | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    init();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const init = async () => {
    try {
      const me = await api.me();
      setUser(me);
      const chatList = await api.getChats();
      setChats(chatList);
      if (chatList.length > 0) {
        selectChat(chatList[0]);
      }
    } catch {
      router.push("/login");
    } finally {
      setLoading(false);
    }
  };

  const selectChat = async (chat: Chat) => {
    setActiveChat(chat);
    const msgs = await api.getMessages(chat.id);
    setMessages(msgs);
  };

  const newChat = async () => {
    const chat = await api.createChat();
    setChats((prev) => [chat, ...prev]);
    setActiveChat(chat);
    setMessages([]);
  };

  const send = async () => {
    if (!input.trim() || sending) return;
    let chat = activeChat;
    if (!chat) {
      chat = await api.createChat();
      setChats((prev) => [chat!, ...prev]);
      setActiveChat(chat);
    }

    const content = input.trim();
    setInput("");
    setSending(true);

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content,
      source: null,
      knowledge_item_id: null,
      used_documents: null,
      tokens_used: null,
      response_time_ms: null,
      rating: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const res = await api.sendMessage(chat.id, content);
      setMessages((prev) => [...prev, res.message]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `Ошибка: ${err instanceof Error ? err.message : "не удалось получить ответ"}`,
          source: "error",
          knowledge_item_id: null,
          used_documents: null,
          tokens_used: null,
          response_time_ms: null,
          rating: null,
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const uploadFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await api.uploadDocument(file, file.name);
      alert("Документ загружен и проиндексирован");
    } catch (err) {
      alert(err instanceof Error ? err.message : "Ошибка загрузки");
    }
    e.target.value = "";
  };

  const logout = () => {
    api.logout();
    router.push("/");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="animate-spin text-brand-600" size={32} />
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      <aside className="w-72 bg-[var(--sidebar)] text-white flex flex-col">
        <div className="p-4 border-b border-white/10">
          <Link href="/" className="flex items-center gap-2 hover:opacity-90 transition">
            <Shield size={24} />
            <div>
              <h1 className="font-bold">Expert17025</h1>
              <p className="text-xs text-white/60">ГОСТ 17025 • Аккредитация</p>
            </div>
          </Link>
        </div>

        <button
          onClick={newChat}
          className="m-3 flex items-center gap-2 px-4 py-2.5 bg-white/10 hover:bg-white/20 rounded-lg transition text-sm"
        >
          <Plus size={18} /> Новый чат
        </button>

        <div className="flex-1 overflow-y-auto px-2">
          {chats.map((chat) => (
            <button
              key={chat.id}
              onClick={() => selectChat(chat)}
              className={`w-full text-left px-3 py-2.5 rounded-lg mb-1 text-sm flex items-center gap-2 transition ${
                activeChat?.id === chat.id ? "bg-white/20" : "hover:bg-white/10"
              }`}
            >
              <MessageSquare size={16} className="shrink-0 opacity-60" />
              <span className="truncate">{chat.title}</span>
            </button>
          ))}
        </div>

        <div className="p-3 border-t border-white/10">
          <p className="text-xs text-white/60 truncate mb-2">{user?.email}</p>
          <div className="flex gap-2">
            <button
              onClick={() => fileRef.current?.click()}
              className="flex-1 flex items-center justify-center gap-1 px-2 py-2 bg-white/10 hover:bg-white/20 rounded text-xs"
            >
              <Upload size={14} /> Документ
            </button>
            <button
              onClick={logout}
              className="px-3 py-2 bg-white/10 hover:bg-white/20 rounded"
              title="Выйти"
            >
              <LogOut size={14} />
            </button>
          </div>
          <input ref={fileRef} type="file" className="hidden" onChange={uploadFile} />
        </div>
      </aside>

      <main className="flex-1 flex flex-col">
        <header className="px-6 py-4 border-b border-slate-200 bg-white">
          <h2 className="font-semibold text-slate-800">
            {activeChat?.title || "Задайте вопрос по аккредитации"}
          </h2>
          <p className="text-sm text-slate-500">
            Сначала поиск по базе знаний, затем RAG + ИИ при необходимости
          </p>
        </header>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          {messages.length === 0 && (
            <div className="max-w-2xl mx-auto mt-16 text-center">
              <h3 className="text-xl font-semibold text-slate-700 mb-4">
                Чем могу помочь?
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {[
                  "Требования п. 7.7 ГОСТ 17025 к ВЛК",
                  "Как оформить область аккредитации?",
                  "Расчёт неопределённости измерений",
                  "Корректирующие действия по замечаниям эксперта",
                ].map((q) => (
                  <button
                    key={q}
                    onClick={() => setInput(q)}
                    className="text-left p-4 rounded-xl border border-slate-200 hover:border-brand-300 hover:bg-brand-50 text-sm transition"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}

          {sending && (
            <div className="flex items-center gap-2 text-slate-500 text-sm mb-4">
              <Loader2 size={16} className="animate-spin" />
              Поиск в базе знаний...
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="p-4 border-t border-slate-200 bg-white">
          <div className="max-w-4xl mx-auto flex gap-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              placeholder="Задайте вопрос по ГОСТ 17025, аккредитации, метрологии..."
              rows={2}
              className="flex-1 resize-none px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
            <button
              onClick={send}
              disabled={sending || !input.trim()}
              className="px-5 py-3 bg-brand-600 text-white rounded-xl hover:bg-brand-700 disabled:opacity-50 transition self-end"
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
