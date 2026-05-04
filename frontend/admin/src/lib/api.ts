/**
 * API client for Django backend with JWT authentication.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface TokenPair {
  access: string;
  refresh: string;
}

function getTokens(): TokenPair | null {
  if (typeof window === "undefined") return null;
  const access = localStorage.getItem("access_token");
  const refresh = localStorage.getItem("refresh_token");
  if (!access || !refresh) return null;
  return { access, refresh };
}

function setTokens(tokens: TokenPair) {
  localStorage.setItem("access_token", tokens.access);
  localStorage.setItem("refresh_token", tokens.refresh);
}

export function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

export function isAuthenticated(): boolean {
  return !!getTokens()?.access;
}

async function refreshAccessToken(): Promise<string | null> {
  const tokens = getTokens();
  if (!tokens?.refresh) return null;

  try {
    const res = await fetch(`${API_URL}/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: tokens.refresh }),
    });
    if (!res.ok) return null;
    const data = await res.json();
    setTokens({ access: data.access, refresh: data.refresh || tokens.refresh });
    return data.access;
  } catch {
    return null;
  }
}

export async function login(username: string, password: string): Promise<boolean> {
  const res = await fetch(`${API_URL}/auth/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) return false;
  const data = await res.json();
  setTokens({ access: data.access, refresh: data.refresh });
  return true;
}

export async function apiFetch<T = Record<string, unknown>>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  let tokens = getTokens();
  if (!tokens?.access) throw new Error("Not authenticated");

  const doFetch = async (token: string) => {
    const res = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        ...options.headers,
      },
    });
    return res;
  };

  let res = await doFetch(tokens.access);

  // Try refresh if 401
  if (res.status === 401) {
    const newToken = await refreshAccessToken();
    if (!newToken) {
      clearTokens();
      window.location.href = "/login";
      throw new Error("Session expired");
    }
    res = await doFetch(newToken);
  }

  // 403 means the session/token is no longer valid — redirect to login
  if (res.status === 403) {
    clearTokens();
    window.location.href = "/login";
    throw new Error("Session expired");
  }

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json();
}
