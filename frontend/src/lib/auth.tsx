import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { Inversor } from "./api";

type AuthCtx = { user: Inversor | null; ready: boolean; signIn: (u: Inversor) => void; signOut: () => void };
const Ctx = createContext<AuthCtx>({ user: null, ready: false, signIn: () => {}, signOut: () => {} });
const KEY = "invertix_user";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Inversor | null>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const raw = localStorage.getItem(KEY);
    if (raw) setUser(JSON.parse(raw));
    setReady(true);
  }, []);
  return (
    <Ctx.Provider
      value={{
        user,
        ready,
        signIn: (u) => { localStorage.setItem(KEY, JSON.stringify(u)); setUser(u); },
        signOut: () => { localStorage.removeItem(KEY); setUser(null); },
      }}
    >
      {children}
    </Ctx.Provider>
  );
}
export const useAuth = () => useContext(Ctx);
