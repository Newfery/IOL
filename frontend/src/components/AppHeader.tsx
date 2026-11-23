import { Link, useNavigate } from "@tanstack/react-router";
import { ChartPie, House, TrendingUp, Users, Wallet } from "lucide-react";
import { useAuth } from "@/lib/auth";

export function AppHeader() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const cls = "inline-flex items-center gap-2 whitespace-nowrap hover:text-foreground";
  const active = { className: "text-foreground" };
  return (
    <header className="border-b border-border">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <Link to="/" className="font-display text-2xl font-bold tracking-tight">
          inverti<span className="text-primary">x</span>
        </Link>
        <nav className="hidden items-center gap-4 text-sm text-muted-foreground md:flex lg:gap-6">
          <Link to="/" className={cls} activeProps={active} activeOptions={{ exact: true }}>
            <House className="size-4 shrink-0" aria-hidden="true" />
            Inicio
          </Link>
          <Link to="/operar" className={cls} activeProps={active}>
            <TrendingUp className="size-4 shrink-0" aria-hidden="true" />
            Invertir
          </Link>
          <Link to="/mis-inversiones" className={cls} activeProps={active}>
            <ChartPie className="size-4 shrink-0" aria-hidden="true" />
            Mis inversiones
          </Link>
          <Link to="/mi-dinero" className={cls} activeProps={active}>
            <Wallet className="size-4 shrink-0" aria-hidden="true" />
            Mi dinero
          </Link>
          <Link to="/grupos" className={cls} activeProps={active}>
            <Users className="size-4 shrink-0" aria-hidden="true" />
            Grupos de inversión
          </Link>
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
