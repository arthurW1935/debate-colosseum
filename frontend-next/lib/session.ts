"use client";

let refreshInterval: NodeJS.Timeout | null = null;

export async function validateSession(): Promise<boolean> {
  const token = localStorage.getItem("token");
  if (!token) return false;

  try {
    const res = await fetch("http://localhost:8000/auth/me", {
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });
    return res.ok;
  } catch (error) {
    console.error("Session validation error:", error);
    return false;
  }
}

export async function refreshSession() {
  const token = localStorage.getItem("token");
  if (!token) return;

  try {
    await fetch("http://localhost:8000/auth/me", {
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });
  } catch (error) {
    console.error("Session refresh error:", error);
  }
}

export function handleSessionExpired() {
  localStorage.removeItem("token");
  window.location.href = "/login?expired=true";
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
