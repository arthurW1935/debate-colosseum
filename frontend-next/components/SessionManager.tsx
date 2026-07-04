"use client";

import { useEffect } from "react";
import { validateSession, startSessionRefresh, stopSessionRefresh, handleSessionExpired } from "@/lib/session";
import { getToken } from "@/lib/auth";
import { usePathname } from "next/navigation";

export default function SessionManager() {
  const pathname = usePathname();

  useEffect(() => {
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      const response = await originalFetch(...args);
      if (response.status === 401) {
        handleSessionExpired();
      }
      return response;
    };

    const checkSession = async () => {
      if (getToken()) {
        const isValid = await validateSession();
        if (!isValid) {
          handleSessionExpired();
        } else {
          startSessionRefresh();
        }
      }
    };

    checkSession();

    return () => {
      stopSessionRefresh();
      window.fetch = originalFetch;
    };
  }, [pathname]);

  return null;
}
