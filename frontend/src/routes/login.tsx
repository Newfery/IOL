import { createFileRoute, Navigate, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { login } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Iniciar sesión — Invertix" },
      { name: "description", content: "Ingresá a tu cuenta de Invertix para ver tu saldo y tus inversiones." },
      { property: "og:title", content: "Iniciar sesión — Invertix" },
      { property: "og:description", content: "Ingresá a tu cuenta de Invertix." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Login,
});

function Login() {
  const { user, ready, signIn } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (ready && user) return <Navigate to="/" replace />;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const session = await login(email, password);
      signIn(session.inversor);
      navigate({ to: "/", replace: true });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 text-foreground">
      <form onSubmit={submit} className="w-full max-w-sm space-y-4 rounded-xl border border-border bg-card p-8">
        <div className="text-center">
          <h1 className="font-display text-3xl font-bold">inverti<span className="text-primary">x</span></h1>
          <p className="mt-2 text-sm text-muted-foreground">Iniciá sesión para continuar</p>
        </div>
        <div>
          <label className="text-xs text-muted-foreground">Email</label>
          <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2" />
        </div>
        <div>
          <label className="text-xs text-muted-foreground">Contraseña</label>
          <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2" />
        </div>
        {error && <p className="text-sm text-loss">{error}</p>}
        <button disabled={loading} className="w-full rounded-md bg-primary py-2 font-semibold text-primary-foreground disabled:opacity-60">
          {loading ? "Ingresando..." : "Ingresar"}
        </button>
      </form>
    </div>
  );
}
