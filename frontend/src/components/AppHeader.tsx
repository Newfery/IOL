import { Link, useNavigate } from "@tanstack/react-router";
import { useAuth } from "@/lib/auth";

export function AppHeader() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const cls = "hover:text-foreground";
  const active = { className: "text-foreground" };
  return (
    <header className="border-b border-border">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <Link to="/" className="font-display text-2xl font-bold tracking-tight">
          inverti<span className="text-primary">x</span>
        </Link>
        <nav className="hidden gap-6 text-sm text-muted-foreground md:flex">
          <Link to="/" className={cls} activeProps={active} activeOptions={{ exact: true }}>Inicio</Link>
          <Link to="/operar" className={cls} activeProps={active}>Invertir</Link>
          <Link to="/mis-inversiones" className={cls} activeProps={active}>Mis inversiones</Link>
          <Link to="/mi-dinero" className={cls} activeProps={active}>Mi dinero</Link>
          <Link to="/grupos" className={cls} activeProps={active}>Grupos de inversión</Link>
        </nav>
        {user && (
          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-muted-foreground sm:inline">Hola, {user.nombre}</span>
            <button
              onClick={() => { signOut(); navigate({ to: "/login", replace: true }); }}
              className="rounded-md border border-border px-3 py-2 text-sm hover:bg-muted"
            >
              Salir
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
