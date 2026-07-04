'use client';
export function saveToken(token: string) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('auth_token', token);
  }
}

export function getToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('auth_token');
  }
  return null;
}

export function removeToken() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('auth_token');
  }
}

export function getUserFromToken(): { id: string; email: string; name: string } | null {
  const token = getToken();
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    if (payload.exp * 1000 < Date.now()) {
      removeToken();
      return null;
    }
    return { id: payload.sub, email: payload.email, name: payload.name };
  } catch {
    return null;
  }
}

export function isLoggedIn(): boolean {
  return getUserFromToken() !== null;
}

export function getAuthHeaders(): HeadersInit {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}
