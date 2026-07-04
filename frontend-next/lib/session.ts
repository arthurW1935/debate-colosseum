"use client";

import { getAuthHeaders, getToken, removeToken } from './auth';

let refreshInterval: NodeJS.Timeout | null = null;
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000';

export async function validateSession(): Promise<boolean> {
  if (!getToken()) return false;

  try {
    const res = await fetch(`${API_BASE}/auth/me`, { headers: getAuthHeaders() });
    return res.ok;
  } catch (error) {
    console.error("Session validation error:", error);
    return false;
  }
}

export async function refreshSession() {
  if (!getToken()) return;

  try {
    await fetch(`${API_BASE}/api/sessions/me`, { headers: getAuthHeaders() });
  } catch (error) {
    console.error("Session refresh error:", error);
  }
}

export async function logoutCurrentSession() {
  if (!getToken()) return;

  try {
    await fetch(`${API_BASE}/api/sessions/logout`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
  } catch (error) {
    console.error("Session logout error:", error);
  }
}

export function handleSessionExpired() {
  removeToken();
  window.location.href = "/";
}

export function startSessionRefresh() {
  if (refreshInterval) return;
  // Refresh every 5 minutes
  refreshInterval = setInterval(async () => {
    const valid = await validateSession();
    if (!valid) {
      stopSessionRefresh();
      handleSessionExpired();
    }
  }, 300000);
}

export function stopSessionRefresh() {
  if (refreshInterval) {
    clearInterval(refreshInterval);
    refreshInterval = null;
  }
}
