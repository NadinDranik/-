const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
}

export interface Chat {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  role: string;
  content: string;
  source: string | null;
  knowledge_item_id: string | null;
  used_documents: unknown[] | null;
  tokens_used: number | null;
  response_time_ms: number | null;
  rating: number | null;
  created_at: string;
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Ошибка запроса");
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  register: (email: string, password: string, full_name?: string) =>
    request<User>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    }),

  login: async (email: string, password: string) => {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);
    const res = await fetch(`${API_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
    });
    if (!res.ok) throw new Error("Неверный email или пароль");
    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    return data;
  },

  logout: () => localStorage.removeItem("token"),

  me: () => request<User>("/api/auth/me"),

  getChats: () => request<Chat[]>("/api/chats"),

  createChat: (title?: string) =>
    request<Chat>("/api/chats", { method: "POST", body: JSON.stringify({ title }) }),

  getMessages: (chatId: string) => request<Message[]>(`/api/chats/${chatId}/messages`),

  sendMessage: (chatId: string, content: string) =>
    request<{ message: Message; source: string; relevance_score: number | null }>(
      `/api/chats/${chatId}/messages`,
      { method: "POST", body: JSON.stringify({ content }) }
    ),

  uploadDocument: (file: File, title: string, category?: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("title", title);
    form.append("scope", "personal");
    if (category) form.append("category", category);
    return request("/api/documents/upload", { method: "POST", body: form });
  },
};
