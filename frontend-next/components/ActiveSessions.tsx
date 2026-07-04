"use client";

import { useEffect, useState } from "react";

type SessionInfo = {
  id: string;
  created_at: string;
  last_active_at: string;
  ip_address: string | null;
  user_agent: string | null;
  is_current: boolean;
};

export default function ActiveSessions() {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchSessions = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;
    
    try {
      const res = await fetch("http://localhost:8000/auth/sessions", {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSessions(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const handleRevoke = async (id: string) => {
    const token = localStorage.getItem("token");
    await fetch(`http://localhost:8000/auth/sessions/${id}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${token}` }
    });
    fetchSessions();
  };

  const handleRevokeAll = async () => {
    const token = localStorage.getItem("token");
    await fetch(`http://localhost:8000/auth/logout-all`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}` }
    });
    fetchSessions();
  };

  const parseDevice = (ua: string | null) => {
    if (!ua) return "Unknown Device";
    if (ua.includes("Windows")) return "Windows PC";
    if (ua.includes("Mac OS")) return "Mac";
    if (ua.includes("iPhone")) return "iPhone";
    if (ua.includes("Android")) return "Android";
    return "Unknown Device";
  };

  if (loading) return <div className="text-gray-400">Loading sessions...</div>;

  return (
    <div className="bg-[#0a0a0f] text-white p-6 rounded-xl border border-gray-800/50 backdrop-blur-md shadow-2xl max-w-3xl w-full">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">Active Sessions</h2>
        <button 
          onClick={handleRevokeAll}
          className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg text-sm transition-colors border border-red-500/20"
        >
          Sign out all other devices
        </button>
      </div>

      <div className="space-y-4">
        {sessions.map(s => (
          <div key={s.id} className="flex justify-between items-center p-4 rounded-lg bg-white/5 border border-white/10 hover:border-indigo-500/30 transition-colors">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-medium">{parseDevice(s.user_agent)}</span>
                {s.is_current && <span className="text-xs bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-full border border-indigo-500/30">Current</span>}
              </div>
              <div className="text-sm text-gray-400 mt-1">
                {s.ip_address || "Unknown IP"} • Last active: {new Date(s.last_active_at).toLocaleString()}
              </div>
            </div>
            {!s.is_current && (
              <button 
                onClick={() => handleRevoke(s.id)}
                className="px-3 py-1.5 text-sm text-gray-400 hover:text-white bg-white/5 hover:bg-white/10 rounded-md transition-colors"
              >
                Sign out
              </button>
            )}
          </div>
        ))}
        {sessions.length === 0 && (
          <div className="text-gray-500 text-center py-4">No active sessions found.</div>
        )}
      </div>
    </div>
  );
}
