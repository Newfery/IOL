import { RequireAuth } from "@/components/RequireAuth";
import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ArrowLeft, ArrowLeftRight, Plus, Search, UserPlus } from "lucide-react";
import { AppHeader } from "@/components/AppHeader";
import { Button } from "@/components/ui/button";
import {
  contributeToGroup,
  createGroup,
  getDolarQuotes,
  getAssets,
  getGroups,
  groupBuy,
  joinGroup,
  type Asset,
  type Group,
  type Moneda,
} from "@/lib/api";
import { CATEGORIES } from "@/lib/categories";

export const Route = createFileRoute("/grupos")({
  head: () => ({
    meta: [
      { title: "Invertix — Grupos de inversión" },
      { name: "description", content: "Creá o unite a un grupo con amigos, junten plata y compren activos entre todos." },
      { property: "og:title", content: "Invertix — Grupos de inversión" },
      { property: "og:description", content: "Invertí en equipo: un pozo común para comprar activos con tus amigos." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => (
    <RequireAuth>
      <Grupos />
    </RequireAuth>
  ),
});

const fmt = (n: number) =>
  n.toLocaleString("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 2 });
const fmtUsd = (n: number) =>
  n.toLocaleString("es-AR", { style: "currency", currency: "USD", maximumFractionDigits: 2 });

const BUY_PAGE_SIZE = 20;

function Grupos() {
  const [groups, setGroups] = useState<Group[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [newName, setNewName] = useState("");
  const [newPass, setNewPass] = useState("");
  const [code, setCode] = useState("");
  const [joinPass, setJoinPass] = useState("");
  const [groupAction, setGroupAction] = useState<"create" | "join" | null>(null);
  const [amount, setAmount] = useState(10000);
  const [currency, setCurrency] = useState<Moneda>("ARS");
  const [summaryCurrency, setSummaryCurrency] = useState<Moneda>("ARS");
  const [mep, setMep] = useState<number | null>(null);
  const [quoteError, setQuoteError] = useState("");
  const [symbol, setSymbol] = useState("");
  const [qty, setQty] = useState(1);
  const [buyScreen, setBuyScreen] = useState(false);
  const [buySearch, setBuySearch] = useState("");
  const [buyCategory, setBuyCategory] = useState("todos");
  const [buyPage, setBuyPage] = useState(1);
  const [msg, setMsg] = useState("");
  const [groupsLoading, setGroupsLoading] = useState(true);
  const [groupsError, setGroupsError] = useState("");
  const [assetsError, setAssetsError] = useState("");

  const refresh = async (selectId?: string) => {
    setGroupsLoading(true);
    setGroupsError("");
    try {
      const g = await getGroups();
      setGroups([...g]);
      setActiveId((cur) => selectId ?? cur ?? g[0]?.id ?? null);
    } catch (error) {
      setGroupsError(error instanceof Error ? error.message : "No se pudieron cargar tus grupos.");
    } finally {
      setGroupsLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    getAssets().then((availableAssets) => {
      setAssets(availableAssets);
      setSymbol(availableAssets[0]?.symbol ?? "");
    }).catch((error: unknown) => {
      setAssetsError(error instanceof Error ? error.message : "No se pudieron cargar los activos.");
    });
    getDolarQuotes()
      .then((quotes) => setMep(quotes.mep))
      .catch((error: unknown) => {
        setQuoteError(error instanceof Error ? error.message : "No se pudo obtener MEP.");
      });
  }, []);

  const group = groups.find((g) => g.id === activeId) ?? null;
  const asset = assets.find((a) => a.symbol === symbol);
  const totalPool = group ? group.members.reduce((s, m) => s + m.contributed, 0) : 0;
  const exchangeRate = mep !== null && mep > 0 ? mep : null;
  const formatSummaryAmount = (value: number) =>
    summaryCurrency === "ARS"
      ? fmt(value)
      : exchangeRate === null ? "No disponible" : fmtUsd(value / exchangeRate);
  const estimatedBuyTotal =
    asset ? asset.price * qty * 1.005 : null;
  const estimatedBuyDebitARS =
    !asset
      ? null
      : asset.currency === "USD"
        ? exchangeRate === null ? null : asset.price * qty * exchangeRate * 1.005
        : asset.price * qty * 1.005;
  const selectedBuyCategory = CATEGORIES.find((category) => category.slug === buyCategory);
  const buyQuery = buySearch.trim().toLowerCase();
  const matchingBuyAssets = assets.filter((availableAsset) =>
    (!selectedBuyCategory || selectedBuyCategory.matches(availableAsset))
    && (!buyQuery
      || availableAsset.symbol.toLowerCase().includes(buyQuery)
      || availableAsset.name.toLowerCase().includes(buyQuery)),
  );
  const buyPageCount = Math.ceil(matchingBuyAssets.length / BUY_PAGE_SIZE);
  const currentBuyPage = Math.min(buyPage, Math.max(1, buyPageCount));
  const buyPageAssets = matchingBuyAssets.slice(
    (currentBuyPage - 1) * BUY_PAGE_SIZE,
    currentBuyPage * BUY_PAGE_SIZE,
  );
  const buyCategories = CATEGORIES.filter((category) => category.type !== "Favoritos");

  async function onCreate() {
    if (!newName.trim()) return setMsg("Poné un nombre para el grupo.");
    if (newPass.length < 4) return setMsg("La contraseña debe tener al menos 4 caracteres.");
    let g;
    try {
      g = await createGroup(newName.trim(), newPass);
    } catch (e) {
      return setMsg((e as Error).message);
    }
    setNewName("");
    setNewPass("");
    setMsg(`Grupo creado. Compartí el nombre "${g.name}" y la contraseña con tus amigos.`);
    setGroupAction(null);
    refresh(g.id);
  }
  async function onJoin() {
    let g;
    try {
      g = await joinGroup(code.trim(), joinPass);
    } catch (e) {
      return setMsg((e as Error).message);
    }
    setCode("");
    setJoinPass("");
    setMsg(`Te uniste a "${g.name}".`);
    setGroupAction(null);
    refresh(g.id);
  }
  async function onContribute() {
    if (!group) return;
    if (!Number.isFinite(amount) || amount <= 0) {
      setMsg("Poné un monto mayor a cero.");
      return;
    }
    try {
      await contributeToGroup(group.id, amount, currency);
      setMsg(`Aportaste ${currency === "ARS" ? fmt(amount) : fmtUsd(amount)} al pozo.`);
      await refresh();
    } catch (e) {
      setMsg((e as Error).message);
    }
  }
  async function onBuy() {
    if (!group || !asset) return;
    try {
      await groupBuy(group.id, asset.symbol, qty);
      setMsg(`Compra grupal: ${qty} ${asset.symbol}.`);
      refresh();
    } catch (e) {
      setMsg((e as Error).message);
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <AppHeader />
      <main className="mx-auto max-w-7xl space-y-8 px-6 py-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="font-display text-3xl font-bold">Grupos de inversión</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Juntá plata con amigos o conocidos y compren activos entre todos.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setGroupAction("create")}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
            >
              <Plus className="size-4" />
              Crear
            </button>
            <button
              type="button"
              onClick={() => setGroupAction("join")}
              className="inline-flex items-center gap-2 rounded-md border border-border bg-card px-4 py-2 text-sm font-semibold"
            >
              <UserPlus className="size-4" />
              Unirse
            </button>
          </div>
        </div>

        {groupAction === "create" && (
          <section className="ml-auto max-w-xl rounded-xl border border-border bg-card p-5">
            <div className="flex items-start justify-between gap-4">
              <h2 className="font-display text-lg font-semibold">Crear un grupo</h2>
              <button type="button" onClick={() => setGroupAction(null)} className="text-sm text-muted-foreground hover:text-foreground">
                Cerrar
              </button>
            </div>
            <div className="mt-3 flex flex-col gap-2 sm:flex-row">
              <input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Nombre del grupo"
                className="min-w-0 flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm" />
              <input type="password" value={newPass} onChange={(e) => setNewPass(e.target.value)} placeholder="Contraseña para unirse"
                className="min-w-0 flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm" />
              <button type="button" onClick={onCreate} className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground">Crear</button>
            </div>
          </section>
        )}

        {groupAction === "join" && (
          <section className="ml-auto max-w-xl rounded-xl border border-border bg-card p-5">
            <div className="flex items-start justify-between gap-4">
              <h2 className="font-display text-lg font-semibold">Unirme a un grupo</h2>
              <button type="button" onClick={() => setGroupAction(null)} className="text-sm text-muted-foreground hover:text-foreground">
                Cerrar
              </button>
            </div>
            <div className="mt-3 flex flex-col gap-2 sm:flex-row">
              <input value={code} onChange={(e) => setCode(e.target.value)} placeholder="Nombre del grupo"
                className="min-w-0 flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm" />
              <input type="password" value={joinPass} onChange={(e) => setJoinPass(e.target.value)} placeholder="Contraseña"
                className="min-w-0 flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm" />
              <button type="button" onClick={onJoin} className="rounded-md bg-secondary px-4 py-2 text-sm font-semibold">Unirse</button>
            </div>
          </section>
        )}

        {msg && <p className="text-sm text-primary">{msg}</p>}
        {groupsError && (
          <p role="alert" className="flex flex-wrap items-center gap-3 text-sm text-loss">
            {groupsError}
            <button type="button" onClick={() => void refresh()} className="underline">
              Reintentar
            </button>
          </p>
        )}

        <section className="grid gap-6 lg:grid-cols-4">
          <aside className="space-y-2">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Mis grupos</p>
            {groupsLoading && <p role="status" className="text-sm text-muted-foreground">Cargando grupos…</p>}
            {!groupsLoading && !groupsError && groups.length === 0 && (
              <p className="text-sm text-muted-foreground">Todavía no pertenecés a ningún grupo.</p>
            )}
            {groups.map((g) => (
              <button key={g.id} onClick={() => {
                setActiveId(g.id);
                setBuyScreen(false);
              }}
                className={`w-full rounded-lg border border-border p-3 text-left text-sm ${g.id === activeId ? "bg-muted" : "bg-card"}`}>
                <div className="font-semibold">{g.name}</div>
                <div className="text-xs text-muted-foreground">{g.members.length} miembros</div>
              </button>
            ))}
          </aside>

          {group && (
            <div className="space-y-6 lg:col-span-3">
              <div className="space-y-3">
                <div className="flex justify-end">
                  <button
                    type="button"
                    aria-label={`Mostrar pozo y total aportado en ${summaryCurrency === "ARS" ? "USD" : "ARS"}`}
                    onClick={() => setSummaryCurrency((value) => value === "ARS" ? "USD" : "ARS")}
                    className="inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-md transition hover:scale-[1.02] hover:bg-primary/90 hover:shadow-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    <ArrowLeftRight className="size-4" aria-hidden="true" />
                    Ver en {summaryCurrency === "ARS" ? "USD" : "ARS"}
                  </button>
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <Stat
                    label={`Pozo disponible (${summaryCurrency})`}
                    value={formatSummaryAmount(group.cash)}
                  />
                  <Stat
                    label={`Total aportado (${summaryCurrency})`}
                    value={formatSummaryAmount(totalPool)}
                  />
                </div>
              </div>
              {summaryCurrency === "USD" && exchangeRate === null && (
                <p role="status" className="text-xs text-muted-foreground">
                  {quoteError || "No hay una cotización MEP disponible para mostrar el pozo en USD."}
                </p>
              )}

              {buyScreen ? (
                <section className="space-y-5 rounded-xl border border-border bg-card p-5">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <h2 className="font-display text-xl font-semibold">Elegí un activo</h2>
                      <p className="mt-1 text-sm text-muted-foreground">
                        Explorá las categorías o buscá por nombre o símbolo.
                      </p>
                    </div>
                    <Button type="button" variant="outline" onClick={() => setBuyScreen(false)}>
                      <ArrowLeft aria-hidden="true" />
                      Volver al grupo
                    </Button>
                  </div>
                  <div className="relative max-w-md">
                    <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                    <input
                      type="search"
                      aria-label="Buscar activo por nombre o símbolo"
                      value={buySearch}
                      onChange={(event) => {
                        setBuySearch(event.target.value);
                        setBuyPage(1);
                      }}
                      placeholder="Buscar por nombre o símbolo"
                      className="w-full rounded-md border border-input bg-background py-2 pl-9 pr-3 text-sm"
                    />
                  </div>
                  <div className="flex flex-wrap gap-2" role="group" aria-label="Categorías de activos">
                    <Button
                      type="button"
                      size="sm"
                      variant={buyCategory === "todos" ? "default" : "outline"}
                      aria-pressed={buyCategory === "todos"}
                      onClick={() => {
                        setBuyCategory("todos");
                        setBuyPage(1);
                      }}
                    >
                      Todos
                    </Button>
                    {buyCategories.map((category) => (
                      <Button
                        key={category.slug}
                        type="button"
                        size="sm"
                        variant={buyCategory === category.slug ? "default" : "outline"}
                        aria-pressed={buyCategory === category.slug}
                        onClick={() => {
                          setBuyCategory(category.slug);
                          setBuyPage(1);
                        }}
                      >
                        {category.label}
                      </Button>
                    ))}
                  </div>
                  {assetsError && <p role="alert" className="text-sm text-loss">{assetsError}</p>}
                  {buyPageAssets.length > 0 ? (
                    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                      {buyPageAssets.map((availableAsset) => (
                        <article key={availableAsset.symbol} className="flex min-w-0 flex-col justify-between gap-4 rounded-lg border border-border p-4">
                          <div>
                            <p className="font-semibold">{availableAsset.symbol}</p>
                            <p className="mt-1 min-h-10 text-sm text-muted-foreground">{availableAsset.name}</p>
                            <p className="mt-2 text-xs text-muted-foreground">
                              {availableAsset.type} · {availableAsset.currency}
                            </p>
                            <p className="mt-1 font-mono text-sm">
                              {availableAsset.currency === "USD" ? fmtUsd(availableAsset.price) : fmt(availableAsset.price)}
                            </p>
                          </div>
                          <Button
                            type="button"
                            onClick={() => {
                              setSymbol(availableAsset.symbol);
                              setBuyScreen(false);
                            }}
                          >
                            Elegir activo
                          </Button>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <p className="py-8 text-center text-sm text-muted-foreground">
                      {assets.length === 0 ? "No hay activos disponibles." : "No hay activos que coincidan con la búsqueda."}
                    </p>
                  )}
                  {buyPageCount > 1 && (
                    <nav aria-label="Paginación de activos para la compra" className="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
                      <p aria-live="polite" className="text-sm text-muted-foreground">
                        Mostrando {(currentBuyPage - 1) * BUY_PAGE_SIZE + 1}–{Math.min(currentBuyPage * BUY_PAGE_SIZE, matchingBuyAssets.length)} de {matchingBuyAssets.length} activos
                      </p>
                      <div className="flex items-center gap-2">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          disabled={currentBuyPage === 1}
                          onClick={() => setBuyPage(currentBuyPage - 1)}
                        >
                          Anterior
                        </Button>
                        <span className="text-sm">Página {currentBuyPage} de {buyPageCount}</span>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          disabled={currentBuyPage === buyPageCount}
                          onClick={() => setBuyPage(currentBuyPage + 1)}
                        >
                          Siguiente
                        </Button>
                      </div>
                    </nav>
                  )}
                </section>
              ) : (
                <>
              <div className="grid gap-6 md:grid-cols-2">
                <div className="rounded-xl border border-border bg-card p-5">
                  <h2 className="font-display text-lg font-semibold">Miembros y aportes</h2>
                  <ul className="mt-3 space-y-2 text-sm">
                    {group.members.map((m) => (
                      <li key={m.name} className="flex justify-between">
                        <span>{m.name}</span>
                        <span className="font-mono">
                          {fmt(m.contributed)}
                          {m.contributedUsd > 0 && (
                            <span className="ml-1 text-xs text-muted-foreground">
                              ({fmtUsd(m.contributedUsd)} aportados)
                            </span>
                          )}{" "}
                          <span className="text-muted-foreground">
                            ({totalPool ? ((m.contributed / totalPool) * 100).toFixed(0) : 0}%)
                          </span>
                        </span>
                      </li>
                    ))}
                  </ul>
                  <div className="mt-4 flex gap-2">
                    <select
                      value={currency}
                      onChange={(event) => {
                        if (event.target.value === "ARS" || event.target.value === "USD") {
                          const nextCurrency = event.target.value;
                          setCurrency(nextCurrency);
                          setAmount(nextCurrency === "ARS" ? 10000 : 100);
                        }
                      }}
                      className="rounded-md border border-input bg-background px-3 py-2 text-sm">
                      <option value="ARS">ARS</option>
                      <option value="USD">USD</option>
                    </select>
                    <input type="number" min={0.01} step={0.01} value={amount} onChange={(e) => setAmount(Number(e.target.value))}
                      className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm" />
                    <button onClick={onContribute} className="rounded-md bg-primary px-4 text-sm font-semibold text-primary-foreground">Aportar</button>
                  </div>
                  {currency === "USD" && (
                    <p className="mt-2 text-xs text-muted-foreground">
                      {mep
                        ? `Acreditación estimada: ${fmt(amount * mep)} al MEP de ${fmt(mep)}.`
                        : quoteError || "No hay una cotización MEP disponible."}
                    </p>
                  )}
                </div>

                <div className="rounded-xl border border-border bg-card p-5">
                  <h2 className="font-display text-lg font-semibold">Comprar con el pozo</h2>
                  {assetsError && <p role="alert" className="mt-2 text-sm text-loss">{assetsError}</p>}
                  {asset ? (
                    <div className="mt-3 rounded-lg border border-border bg-background p-3">
                      <p className="font-semibold">{asset.symbol} — {asset.name}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{asset.type} · {asset.currency}</p>
                    </div>
                  ) : (
                    <p className="mt-3 text-sm text-muted-foreground">Todavía no elegiste un activo.</p>
                  )}
                  <Button
                    type="button"
                    variant="outline"
                    className="mt-3 w-full"
                    disabled={assets.length === 0}
                    onClick={() => setBuyScreen(true)}
                  >
                    {asset ? "Cambiar activo" : "Elegir activo"}
                  </Button>
                  <input type="number" min={1} value={qty} disabled={!asset} onChange={(e) => setQty(Math.max(1, Number(e.target.value)))}
                    className="mt-2 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
                  <div className="mt-3 flex justify-between text-sm">
                    <span className="text-muted-foreground">
                      Total estimado en {asset?.currency ?? "ARS"} + comisión 0,5%
                    </span>
                    <span className="font-mono">
                      {estimatedBuyTotal === null
                        ? "—"
                        : asset?.currency === "USD" ? fmtUsd(estimatedBuyTotal) : fmt(estimatedBuyTotal)}
                    </span>
                  </div>
                  {asset?.currency === "USD" && (
                    <div className="mt-2 flex justify-between gap-3 text-xs">
                      <span className="text-muted-foreground">Débito aproximado del pozo (ARS)</span>
                      <span className="font-mono">
                        {estimatedBuyDebitARS === null ? "No disponible" : fmt(estimatedBuyDebitARS)}
                      </span>
                    </div>
                  )}
                  {asset?.currency === "USD" && exchangeRate === null && (
                    <p className="mt-2 text-xs text-muted-foreground">
                      {quoteError || "No hay una cotización MEP disponible para estimar el débito en ARS."}
                    </p>
                  )}
                  <button disabled={!asset} onClick={onBuy} className="mt-4 w-full rounded-md bg-gain py-2 font-semibold text-background disabled:cursor-not-allowed disabled:opacity-50">Comprar para el grupo</button>
                </div>
              </div>

              <div className="rounded-xl border border-border bg-card p-5">
                <h2 className="font-display text-lg font-semibold">Cartera del grupo</h2>
                {group.holdings.length === 0 ? (
                  <p className="mt-2 text-sm text-muted-foreground">Todavía no compraron nada.</p>
                ) : (
                  <ul className="mt-3 space-y-2 text-sm">
                    {group.holdings.map((h) => {
                      const p = assets.find((a) => a.symbol === h.symbol)?.price ?? h.avgPrice;
                      const marketValue = p * h.qty;
                      const valueARS = h.currency === "ARS"
                        ? marketValue
                        : exchangeRate === null ? null : marketValue * exchangeRate;
                      const valueUSD = h.currency === "USD"
                        ? marketValue
                        : exchangeRate === null ? null : marketValue / exchangeRate;
                      const pnl = h.avgPrice > 0 ? ((p - h.avgPrice) / h.avgPrice) * 100 : 0;
                      return (
                        <li key={h.symbol} className="flex justify-between gap-4 border-t border-border pt-3">
                          <span className="shrink-0">
                            <b>{h.symbol}</b> <span className="text-muted-foreground">x{h.qty}</span>
                          </span>
                          <span className="text-right font-mono">
                            <span className="block">{valueARS === null ? "ARS —" : fmt(valueARS)}</span>
                            <span className="block text-muted-foreground">
                              {valueUSD === null ? "USD —" : fmtUsd(valueUSD)}
                            </span>
                            <span className={pnl >= 0 ? "text-gain" : "text-loss"}>{pnl.toFixed(1)}%</span>
                          </span>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
                </>
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-2 font-display text-2xl font-semibold">{value}</p>
    </div>
  );
}
