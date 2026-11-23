import { RequireAuth } from "@/components/RequireAuth";
import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ArrowLeftRight } from "lucide-react";
import { AppHeader } from "@/components/AppHeader";
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

export const Route = createFileRoute("/grupos")({
  head: () => ({
    meta: [
      { title: "Grupos de inversión — Invertix" },
      { name: "description", content: "Creá o unite a un grupo con amigos, junten plata y compren activos entre todos." },
      { property: "og:title", content: "Grupos de inversión — Invertix" },
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

function Grupos() {
  const [groups, setGroups] = useState<Group[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [newName, setNewName] = useState("");
  const [newPass, setNewPass] = useState("");
  const [code, setCode] = useState("");
  const [joinPass, setJoinPass] = useState("");
  const [amount, setAmount] = useState(10000);
  const [currency, setCurrency] = useState<Moneda>("ARS");
  const [summaryCurrency, setSummaryCurrency] = useState<Moneda>("ARS");
  const [mep, setMep] = useState<number | null>(null);
  const [quoteError, setQuoteError] = useState("");
  const [symbol, setSymbol] = useState("");
  const [qty, setQty] = useState(1);
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
        <div>
          <h1 className="font-display text-3xl font-bold">Grupos de inversión</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Juntá plata con amigos o conocidos y compren activos entre todos.
          </p>
        </div>

        <section className="grid gap-4 md:grid-cols-2">
          <div className="rounded-xl border border-border bg-card p-5">
            <h2 className="font-display text-lg font-semibold">Crear un grupo</h2>
            <div className="mt-3 flex gap-2">
              <div className="flex flex-1 flex-col gap-2">
                <input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Nombre del grupo"
                  className="rounded-md border border-input bg-background px-3 py-2 text-sm" />
                <input type="password" value={newPass} onChange={(e) => setNewPass(e.target.value)} placeholder="Contraseña para unirse"
                  className="rounded-md border border-input bg-background px-3 py-2 text-sm" />
              </div>
              <button onClick={onCreate} className="rounded-md bg-primary px-4 text-sm font-semibold text-primary-foreground">Crear</button>
            </div>
          </div>
          <div className="rounded-xl border border-border bg-card p-5">
            <h2 className="font-display text-lg font-semibold">Unirme a un grupo</h2>
            <div className="mt-3 flex gap-2">
              <div className="flex flex-1 flex-col gap-2">
                <input value={code} onChange={(e) => setCode(e.target.value)} placeholder="Nombre del grupo"
                  className="rounded-md border border-input bg-background px-3 py-2 text-sm" />
                <input type="password" value={joinPass} onChange={(e) => setJoinPass(e.target.value)} placeholder="Contraseña"
                  className="rounded-md border border-input bg-background px-3 py-2 text-sm" />
              </div>
              <button onClick={onJoin} className="rounded-md bg-secondary px-4 text-sm font-semibold">Unirme</button>
            </div>
          </div>
        </section>

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
              <button key={g.id} onClick={() => setActiveId(g.id)}
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
                  <select value={symbol} onChange={(e) => setSymbol(e.target.value)}
                    className="mt-3 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                    {assets.map((a) => (
                      <option key={a.symbol} value={a.symbol}>
                        {a.symbol} — {a.name} ({a.symbol.endsWith(".US") ? "EE. UU. · USD" : a.currency})
                      </option>
                    ))}
                  </select>
                  <input type="number" min={1} value={qty} onChange={(e) => setQty(Math.max(1, Number(e.target.value)))}
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
                  <button onClick={onBuy} className="mt-4 w-full rounded-md bg-gain py-2 font-semibold text-background">Comprar para el grupo</button>
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
