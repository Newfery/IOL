import { Link, useNavigate } from "@tanstack/react-router";
import { ChartPie, House, Menu, TrendingUp, Users, Wallet } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { Sheet, SheetClose, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";

export function AppHeader() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const cls = "inline-flex items-center gap-2 whitespace-nowrap hover:text-foreground";
  const active = { className: "text-foreground" };
  const links = [
    { to: "/", label: "Inicio", icon: House, exact: true },
    { to: "/operar", label: "Invertir", icon: TrendingUp },
    { to: "/mis-inversiones", label: "Mis inversiones", icon: ChartPie },
    { to: "/mi-dinero", label: "Mi dinero", icon: Wallet },
    { to: "/grupos", label: "Grupos de inversión", icon: Users },
  ] as const;

  return (
    <header className="border-b border-border">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-3 sm:px-6 sm:py-4">
        <Link to="/" className="shrink-0 font-display text-xl font-bold tracking-tight sm:text-2xl">
          inverti<span className="text-primary">x</span>
        </Link>
        <nav className="hidden items-center gap-4 text-sm text-muted-foreground lg:flex">
          {links.map(({ to, label, icon: Icon, exact }) => (
            <Link
              key={to}
              to={to}
              className={cls}
              activeProps={active}
              activeOptions={exact ? { exact: true } : undefined}
            >
              <Icon className="size-4 shrink-0" aria-hidden="true" />
              {label}
            </Link>
          ))}
        </nav>
        <div className="ml-auto flex shrink-0 items-center gap-2 sm:gap-3 lg:ml-0">
          <Sheet>
            <SheetTrigger asChild>
              <button
                type="button"
                aria-label="Abrir menú de navegación"
                className="inline-flex size-10 items-center justify-center rounded-md border border-border text-muted-foreground hover:bg-muted hover:text-foreground lg:hidden"
              >
                <Menu className="size-5" aria-hidden="true" />
              </button>
            </SheetTrigger>
            <SheetContent side="right" className="w-80 max-w-[85vw]">
              <SheetHeader className="text-left">
                <SheetTitle>Navegación</SheetTitle>
              </SheetHeader>
              <nav className="mt-6 flex flex-col gap-2">
                {links.map(({ to, label, icon: Icon, exact }) => (
                  <SheetClose asChild key={to}>
                    <Link
                      to={to}
                      className="inline-flex min-h-11 items-center gap-3 rounded-md px-3 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
                      activeProps={active}
                      activeOptions={exact ? { exact: true } : undefined}
                    >
                      <Icon className="size-4 shrink-0" aria-hidden="true" />
                      {label}
                    </Link>
                  </SheetClose>
                ))}
              </nav>
            </SheetContent>
          </Sheet>
          {user && (
            <>
              <span className="hidden text-sm text-muted-foreground sm:inline">Hola, {user.nombre}</span>
              <button
                onClick={() => {
                  signOut();
                  navigate({ to: "/login", replace: true });
                }}
                className="rounded-md border border-border px-2.5 py-2 text-sm hover:bg-muted sm:px-3"
              >
                Salir
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
