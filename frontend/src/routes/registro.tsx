import { createFileRoute, Link, Navigate, useNavigate } from "@tanstack/react-router";
import { useState, type FormEvent } from "react";
import { registerInvestor, type PerfilRiesgo } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export const Route = createFileRoute("/registro")({
  head: () => ({
    meta: [
      { title: "Invertix — Crear cuenta" },
      { name: "description", content: "Creá tu cuenta de inversor en Invertix." },
    ],
  }),
  component: Register,
});

function Register() {
  const { user, ready } = useAuth();
  const navigate = useNavigate();
  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [cuit, setCuit] = useState("");
  const [perfilRiesgo, setPerfilRiesgo] = useState<PerfilRiesgo>("moderado");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [created, setCreated] = useState(false);

  if (ready && user) return <Navigate to="/" replace />;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (password !== confirmPassword) {
      setError("Las contraseñas no coinciden.");
      return;
    }

    setLoading(true);
    try {
      await registerInvestor({
        nombre: nombre.trim(),
        email: email.trim(),
        cuit,
        perfil_riesgo: perfilRiesgo,
        password,
      });
      setCreated(true);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo crear la cuenta.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-8 text-foreground">
      <section className="w-full max-w-md space-y-5 rounded-xl border border-border bg-card p-8">
        <div className="text-center">
          <h1 className="font-display text-3xl font-bold">
            inverti<span className="text-primary">x</span>
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">Crear cuenta de inversor</p>
        </div>

        {created ? (
          <div className="space-y-4 text-center">
            <p role="status" className="text-sm text-gain">
              Tu cuenta se creó correctamente. Ya podés iniciar sesión.
            </p>
            <button
              type="button"
              onClick={() => navigate({ to: "/login", replace: true })}
              className="w-full rounded-md bg-primary py-2 font-semibold text-primary-foreground"
            >
              Ir a iniciar sesión
            </button>
          </div>
        ) : (
          <form onSubmit={submit} className="space-y-4">
            <div>
              <label htmlFor="register-name" className="text-xs text-muted-foreground">Nombre y apellido</label>
              <input
                id="register-name"
                autoComplete="name"
                minLength={2}
                required
                value={nombre}
                onChange={(event) => setNombre(event.target.value)}
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2"
              />
            </div>
            <div>
              <label htmlFor="register-email" className="text-xs text-muted-foreground">Email</label>
              <input
                id="register-email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2"
              />
            </div>
            <div>
              <label htmlFor="register-cuit" className="text-xs text-muted-foreground">CUIT (11 dígitos, sin guiones)</label>
              <input
                id="register-cuit"
                type="text"
                inputMode="numeric"
                autoComplete="off"
                pattern="[0-9]{11}"
                maxLength={11}
                minLength={11}
                required
                value={cuit}
                onChange={(event) => setCuit(event.target.value)}
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2"
              />
            </div>
            <div>
              <label htmlFor="register-risk" className="text-xs text-muted-foreground">Perfil de riesgo</label>
              <select
                id="register-risk"
                value={perfilRiesgo}
                onChange={(event) => {
                  const value = event.target.value;
                  if (value === "conservador" || value === "moderado" || value === "agresivo") {
                    setPerfilRiesgo(value);
                  }
                }}
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2"
              >
                <option value="conservador">Conservador</option>
                <option value="moderado">Moderado</option>
                <option value="agresivo">Agresivo</option>
              </select>
            </div>
            <div>
              <label htmlFor="register-password" className="text-xs text-muted-foreground">Contraseña (mínimo 8 caracteres)</label>
              <input
                id="register-password"
                type="password"
                autoComplete="new-password"
                minLength={8}
                maxLength={72}
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2"
              />
            </div>
            <div>
              <label htmlFor="register-confirm-password" className="text-xs text-muted-foreground">Repetir contraseña</label>
              <input
                id="register-confirm-password"
                type="password"
                autoComplete="new-password"
                required
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2"
              />
            </div>
            {error && <p role="alert" className="text-sm text-loss">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-md bg-primary py-2 font-semibold text-primary-foreground disabled:opacity-60"
            >
              {loading ? "Creando cuenta..." : "Crear cuenta"}
            </button>
            <p className="text-center text-sm text-muted-foreground">
              ¿Ya tenés cuenta?{" "}
              <Link to="/login" className="font-semibold text-primary hover:underline">
                Iniciar sesión
              </Link>
            </p>
          </form>
        )}
      </section>
    </div>
  );
}
