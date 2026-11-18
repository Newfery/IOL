// Capa de API. Los endpoints están comentados para completarlos más tarde.
// Mientras tanto se devuelven datos de ejemplo.

export type Asset = {
  symbol: string;
  name: string;
  price: number;
  change: number; // % diario
  type: "Acción" | "CEDEAR" | "Bono" | "FCI";
};

export type Holding = { symbol: string; qty: number; avgPrice: number };

const MOCK_ASSETS: Asset[] = [
  { symbol: "GGAL", name: "Grupo Galicia", price: 6420.5, change: 2.31, type: "Acción" },
  { symbol: "YPFD", name: "YPF", price: 38250, change: -1.12, type: "Acción" },
  { symbol: "PAMP", name: "Pampa Energía", price: 3890, change: 0.84, type: "Acción" },
  { symbol: "AAPL", name: "Apple (CEDEAR)", price: 17850, change: 1.05, type: "CEDEAR" },
  { symbol: "MELI", name: "MercadoLibre (CEDEAR)", price: 21400, change: -0.45, type: "CEDEAR" },
  { symbol: "AL30", name: "Bono AL30", price: 82150, change: 0.32, type: "Bono" },
  { symbol: "GD35", name: "Bono GD35", price: 71300, change: -0.21, type: "Bono" },
];

// Saldo simulado compartido (se reinicia al recargar)
const MOCK_BALANCE = { ars: 1250000, usd: 840 };

const MOCK_HOLDINGS: Holding[] = [
  { symbol: "GGAL", qty: 120, avgPrice: 5800 },
  { symbol: "AAPL", qty: 30, avgPrice: 16200 },
  { symbol: "AL30", qty: 10, avgPrice: 79000 },
];

// const API_URL = import.meta.env.VITE_API_URL;

export async function getAssets(): Promise<Asset[]> {
  // TODO: GET ${API_URL}/api/market/assets
  // const res = await fetch(`${API_URL}/api/market/assets`);
  // return res.json();
  return MOCK_ASSETS;
}

export async function getPortfolio(): Promise<Holding[]> {
  // TODO: GET ${API_URL}/api/portfolio  (requiere token)
  // const res = await fetch(`${API_URL}/api/portfolio`, { headers: { Authorization: `Bearer ${token}` } });
  // return res.json();
  return MOCK_HOLDINGS.map((h) => ({ ...h }));
}

export async function getBalance(): Promise<{ ars: number; usd: number }> {
  // TODO: GET ${API_URL}/api/account/balance
  return { ...MOCK_BALANCE };
}

export type Order = { symbol: string; side: "buy" | "sell"; qty: number; price: number };

export async function placeOrder(order: Order): Promise<{ ok: boolean; id: string }> {
  // TODO: POST ${API_URL}/api/orders
  // const res = await fetch(`${API_URL}/api/orders`, {
  //   method: "POST",
  //   headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
  //   body: JSON.stringify(order),
  // });
  // return res.json();
  const total = order.qty * order.price;
  const h = MOCK_HOLDINGS.find((x) => x.symbol === order.symbol);
  if (order.side === "buy") {
    if (total > MOCK_BALANCE.ars) throw new Error("Saldo insuficiente");
    MOCK_BALANCE.ars -= total;
    if (h) {
      h.avgPrice = (h.avgPrice * h.qty + total) / (h.qty + order.qty);
      h.qty += order.qty;
    } else MOCK_HOLDINGS.push({ symbol: order.symbol, qty: order.qty, avgPrice: order.price });
  } else {
    if (!h || h.qty < order.qty) throw new Error("No tenés suficientes títulos para vender");
    MOCK_BALANCE.ars += total;
    h.qty -= order.qty;
    if (h.qty === 0) MOCK_HOLDINGS.splice(MOCK_HOLDINGS.indexOf(h), 1);
  }
  return { ok: true, id: crypto.randomUUID() };
}

// TODO: POST ${API_URL}/api/auth/login
// export async function login(email: string, password: string) {}

// TODO: GET ${API_URL}/api/market/assets/:symbol/history
// export async function getHistory(symbol: string) {}

// ===== Grupos de inversión =====
export type GroupMember = { name: string; contributed: number };
export type Group = {
  id: string;
  name: string;
  code: string; // código de invitación
  password: string; // contraseña para unirse
  members: GroupMember[];
  cash: number; // saldo del pozo común en ARS
  holdings: Holding[];
};

let MOCK_GROUPS: Group[] = [
  {
    id: "g1",
    name: "Los del asado",
    code: "ASADO24",
    password: "1234",
    members: [
      { name: "Vos", contributed: 150000 },
      { name: "Juli", contributed: 100000 },
      { name: "Tomi", contributed: 50000 },
    ],
    cash: 108000,
    holdings: [{ symbol: "GGAL", qty: 30, avgPrice: 6400 }],
  },
];

export async function getGroups(): Promise<Group[]> {
  // TODO: GET ${API_URL}/api/grupos  (grupos del usuario)
  return MOCK_GROUPS;
}

export async function createGroup(name: string, password: string): Promise<Group> {
  // TODO: POST ${API_URL}/api/grupos  body: { nombre, password }
  if (MOCK_GROUPS.some((x) => x.name.trim().toLowerCase() === name.trim().toLowerCase()))
    throw new Error("Ya existe un grupo con ese nombre.");
  const g: Group = {
    id: crypto.randomUUID(),
    name,
    code: Math.random().toString(36).slice(2, 8).toUpperCase(),
    password,
    members: [{ name: "Vos", contributed: 0 }],
    cash: 0,
    holdings: [],
  };
  MOCK_GROUPS = [...MOCK_GROUPS, g];
  return g;
}

export async function joinGroup(name: string, password: string): Promise<Group> {
  // TODO: POST ${API_URL}/api/grupos/unirse  body: { nombre, password }
  const g = MOCK_GROUPS.find((x) => x.name.trim().toLowerCase() === name.trim().toLowerCase());
  if (!g) throw new Error("No existe un grupo con ese nombre.");
  if (g.password !== password) throw new Error("Contraseña incorrecta.");
  if (!g.members.some((m) => m.name === "Vos")) g.members.push({ name: "Vos", contributed: 0 });
  return g;
}

export async function contributeToGroup(groupId: string, amount: number): Promise<Group> {
  // TODO: POST ${API_URL}/api/grupos/${groupId}/aportes  body: { monto }
  const g = MOCK_GROUPS.find((x) => x.id === groupId)!;
  const me = g.members.find((m) => m.name === "Vos")!;
  me.contributed += amount;
  g.cash += amount;
  return { ...g };
}

export async function groupBuy(groupId: string, symbol: string, qty: number, price: number): Promise<Group> {
  // TODO: POST ${API_URL}/api/grupos/${groupId}/operaciones  body: { ticker, cantidad }
  const g = MOCK_GROUPS.find((x) => x.id === groupId)!;
  const total = qty * price * 1.005; // comisión 0,5%
  if (total > g.cash) throw new Error("El pozo del grupo no alcanza");
  g.cash -= total;
  const h = g.holdings.find((x) => x.symbol === symbol);
  if (h) {
    h.avgPrice = (h.avgPrice * h.qty + price * qty) / (h.qty + qty);
    h.qty += qty;
  } else g.holdings.push({ symbol, qty, avgPrice: price });
  return { ...g };
}

// ===== Inversor / Cuenta / Login =====
export type PerfilRiesgo = "Conservador" | "Moderado" | "Agresivo";
export type Inversor = {
  id: number;
  email: string;
  nombre: string;
  cuit: string;
  perfil_riesgo: PerfilRiesgo;
  fecha_alta: string;
};
export type Cuenta = {
  id: number;
  inversor_id: number;
  numero_comitente: string;
  saldo_ars: number;
  saldo_usd: number;
};

export async function login(email: string, password: string): Promise<Inversor> {
  // TODO: POST ${API_URL}/api/auth/login  body: { email, password }  -> { token, inversor }
  if (!email.includes("@") || password.length < 4) throw new Error("Email o contraseña inválidos");
  const nombre = email.split("@")[0] ?? "";
  return {
    id: 1,
    email,
    nombre: nombre.charAt(0).toUpperCase() + nombre.slice(1),
    cuit: "20-12345678-9",
    perfil_riesgo: "Moderado",
    fecha_alta: "2025-03-10",
  };
}

export async function getCuenta(inversorId: number): Promise<Cuenta> {
  // TODO: GET ${API_URL}/api/inversores/${inversorId}/cuenta
  return { id: 1, inversor_id: inversorId, numero_comitente: "245781", saldo_ars: MOCK_BALANCE.ars, saldo_usd: MOCK_BALANCE.usd };
}

export async function getDolarQuotes(): Promise<{ mep: number; ccl: number }> {
  // TODO: GET ${API_URL}/api/market/dolar  (MEP y CCL)
  return { mep: 1570.38, ccl: 1686.98 };
}
