import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { Inversor } from "./api";

type AuthCtx = { user: Inversor | null; ready: boolean; signIn: (u: Inversor) => void; signOut: () => void };
const Ctx = createContext<AuthCtx>({ user: null, ready: false, signIn: () => {}, signOut: () => {} });
const KEY = "invertix_user";
const TOKEN_KEY = "invertix_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Inversor | null>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    try {
      const raw = localStorage.getItem(KEY);
      const token = localStorage.getItem(TOKEN_KEY);
      if (raw && token) setUser(JSON.parse(raw));
      else {
        localStorage.removeItem(KEY);
        localStorage.removeItem(TOKEN_KEY);
      }
    } catch {
      localStorage.removeItem(KEY);
      localStorage.removeItem(TOKEN_KEY);
    }
    setReady(true);
  }, []);
  return (
    <Ctx.Provider
      value={{
        user,
        ready,
        signIn: (u) => { localStorage.setItem(KEY, JSON.stringify(u)); setUser(u); },
        signOut: () => { localStorage.removeItem(KEY); localStorage.removeItem(TOKEN_KEY); setUser(null); },
      }}
    >
      {children}
    </Ctx.Provider>
  );
}
export const useAuth = () => useContext(Ctx);
