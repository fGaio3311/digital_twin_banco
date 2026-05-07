export const TOKEN_KEY = "dt_token";
export const ROLE_KEY = "dt_role";
export const USERNAME_KEY = "dt_username";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setAuth(token: string, role: string, username: string): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(ROLE_KEY, role);
  localStorage.setItem(USERNAME_KEY, username);
}

export function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
  localStorage.removeItem(USERNAME_KEY);
}

export function getRole(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ROLE_KEY);
}

export function getUsername(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem(USERNAME_KEY) ?? "";
}

export function isAdmin(): boolean {
  return getRole() === "admin";
}
