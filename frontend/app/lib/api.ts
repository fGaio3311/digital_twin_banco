const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("dt_token") : null;

  const incoming = (options.headers ?? {}) as Record<string, string>;
  const headers: Record<string, string> = { ...incoming };
  if (!headers["Content-Type"]) headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    const txt = await res.text().catch(() => String(res.status));
    throw new Error(txt || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const apiBase = BASE;
