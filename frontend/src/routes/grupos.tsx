import { RequireAuth } from "@/components/RequireAuth";
import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import {
  contributeToGroup,
  createGroup,
  getAssets,
  getGroups,
  groupBuy,
  joinGroup,
  type Asset,
  type Group,
} from "@/lib/api";

export const Route = createFileRoute("/grupos")({
  head: () => ({
    meta: [
      { title: "Grupos de inversión — Invertix" },
      { name: "description", content: "Creá o unite a un grupo con amigos, junten plata y compren acciones entre todos." },
      { property: "og:title", content: "Grupos de inversión — Invertix" },
      { property: "og:description", content: "Invertí en equipo: un pozo común para comprar acciones con tus amigos." },
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

function Grupos() {
  const [groups, setGroups] = useState<Group[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [newName, setNewName] = useState("");
  const [newPass, setNewPass] = useState("");
  const [code, setCode] = useState("");
  const [joinPass, setJoinPass] = useState("");
  const [amount, setAmount] = useState(10000);
  const [symbol, setSymbol] = useState("");
  const [qty, setQty] = useState(1);
  const [msg, setMsg] = useState("");

  const refresh = async (selectId?: string) => {
    const g = await getGroups();
    setGroups([...g]);
    setActiveId((cur) => selectId ?? cur ?? g[0]?.id ?? null);
  };

  useEffect(() => {
    refresh();
    getAssets().then((assets) => {
      const arsAssets = assets.filter((asset) => asset.currency === "ARS");
      setAssets(arsAssets);
      setSymbol(arsAssets[0]?.symbol ?? "");
    });
  }, []);

  const group = groups.find((g) => g.id === activeId) ?? null;
  const asset = assets.find((a) => a.symbol === symbol);
  const totalPool = group ? group.members.reduce((s, m) => s + m.contributed, 0) : 0;

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
    if (!group || amount <= 0) return;
    try {
      await contributeToGroup(group.id, amount);
      setMsg(`Aportaste ${fmt(amount)} al pozo.`);
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
            Juntá plata con amigos o conocidos y compren acciones entre todos.
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

        <section className="grid gap-6 lg:grid-cols-4">
          <aside className="space-y-2">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Mis grupos</p>
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
              <div className="grid gap-4 md:grid-cols-2">
                <Stat label="Pozo disponible" value={fmt(group.cash)} />
                <Stat label="Total aportado" value={fmt(totalPool)} />
              </div>

              <div className="grid gap-6 md:grid-cols-2">
                <div className="rounded-xl border border-border bg-card p-5">
                  <h2 className="font-display text-lg font-semibold">Miembros y aportes</h2>
                  <ul className="mt-3 space-y-2 text-sm">
                    {group.members.map((m) => (
                      <li key={m.name} className="flex justify-between">
                        <span>{m.name}</span>
                        <span className="font-mono">
                          {fmt(m.contributed)}{" "}
                          <span className="text-muted-foreground">
                            ({totalPool ? ((m.contributed / totalPool) * 100).toFixed(0) : 0}%)
                          </span>
                        </span>
                      </li>
                    ))}
                  </ul>
                  <div className="mt-4 flex gap-2">
                    <input type="number" min={1} value={amount} onChange={(e) => setAmount(Number(e.target.value))}
                      className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm" />
                    <button onClick={onContribute} className="rounded-md bg-primary px-4 text-sm font-semibold text-primary-foreground">Aportar</button>
                  </div>
                </div>

                <div className="rounded-xl border border-border bg-card p-5">
                  <h2 className="font-display text-lg font-semibold">Comprar con el pozo</h2>
                  <select value={symbol} onChange={(e) => setSymbol(e.target.value)}
                    className="mt-3 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                    {assets.map((a) => <option key={a.symbol} value={a.symbol}>{a.symbol} — {a.name}</option>)}
                  </select>
                  <input type="number" min={1} value={qty} onChange={(e) => setQty(Math.max(1, Number(e.target.value)))}
                    className="mt-2 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
                  <div className="mt-3 flex justify-between text-sm">
                    <span className="text-muted-foreground">Total + comisión 0,5%</span>
                    <span className="font-mono">{asset && fmt(asset.price * qty * 1.005)}</span>
                  </div>
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
                      const pnl = ((p - h.avgPrice) / h.avgPrice) * 100;
                      return (
                        <li key={h.symbol} className="flex justify-between">
                          <span><b>{h.symbol}</b> <span className="text-muted-foreground">x{h.qty}</span></span>
                          <span className="font-mono">{fmt(p * h.qty)} <span className={pnl >= 0 ? "text-gain" : "text-loss"}>{pnl.toFixed(1)}%</span></span>
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
