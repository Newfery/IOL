const API_URL = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ?? "";
const TOKEN_KEY = "invertix_token";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem(TOKEN_KEY);
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...init, headers });
  } catch (reason) {
    const detail = reason instanceof Error ? ` ${reason.message}` : "";
    throw new Error(
      `No se pudo conectar con la API (${API_URL || path}). Verificá que el backend esté activo y que VITE_API_URL/CORS estén configurados.${detail}`,
    );
  }
  if (!response.ok) {
    let message = `Error ${response.status}`;
    try {
      const body = await response.json();
      message = body.detail ?? body.message ?? message;
    } catch { /* respuesta sin JSON */ }
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export type Moneda = "ARS" | "USD";
export type Asset = {
  id: number;
  symbol: string;
  name: string;
  price: number;
  change: number;
  type: "Acción" | "CEDEAR" | "Bono" | "ETF" | "FCI";
  currency: Moneda;
  quoteDate?: string | null;
};
export type Holding = { symbol: string; qty: number; avgPrice: number; currency: Moneda };
export type Favorite = { inversor_id: number; activo_id: number };
export type Order = { symbol: string; side: "buy" | "sell"; qty: number; price: number };
export type HistoryPoint = {
  date: string;
  price: number;
  open?: number;
  high?: number;
  low?: number;
};
export type PerfilRiesgo = "conservador" | "moderado" | "agresivo";
export type Inversor = { id: number; email: string; nombre: string; cuit: string; perfil_riesgo: PerfilRiesgo; fecha_alta: string };
export type RegisterInvestorRequest = Pick<Inversor, "email" | "nombre" | "cuit" | "perfil_riesgo"> & {
  password: string;
};
export type Cuenta = { id: number; inversor_id: number; numero_comitente: string; saldo_ars: number; saldo_usd: number };
export type GroupMember = { name: string; contributed: number; contributedUsd: number };
export type Group = { id: string; name: string; code: string; members: GroupMember[]; cash: number; holdings: Holding[] };
export type DolarQuotes = { mep: number | null; ccl: number | null };
export type CreateMovimientoRequest = {
  cuenta_id: number;
  tipo: "deposito" | "extraccion";
  moneda: Moneda;
  monto: number;
};

export async function login(email: string, password: string): Promise<{ token: string; inversor: Inversor }> {
  const result = await request<{ token?: string; access_token?: string; inversor: Inversor }>("/api/auth/login", {
    method: "POST", body: JSON.stringify({ email, password }),
  });
  const token = result.token ?? result.access_token;
  if (!token || !result.inversor) throw new Error("La respuesta de autenticación no incluye token e inversor.");
  localStorage.setItem(TOKEN_KEY, token);
  return { token, inversor: result.inversor };
}

export async function registerInvestor(investor: RegisterInvestorRequest): Promise<Inversor> {
  return request("/api/inversores/", {
    method: "POST",
    body: JSON.stringify(investor),
  });
}

export async function getFavoriteAssetIds(inversorId: number): Promise<number[]> {
  const favorites = await request<Favorite[]>(`/api/favoritos/inversor/${inversorId}`);
  return favorites.map((favorite) => favorite.activo_id);
}
export async function createFavorite(inversorId: number, activoId: number): Promise<Favorite> {
  return request("/api/favoritos/", {
    method: "POST",
    body: JSON.stringify({ inversor_id: inversorId, activo_id: activoId }),
  });
}
export async function deleteFavorite(inversorId: number, activoId: number): Promise<void> {
  return request(`/api/favoritos/${inversorId}/${activoId}`, { method: "DELETE" });
}

export async function getCuenta(inversorId: number): Promise<Cuenta> { return request(`/api/inversores/${inversorId}/cuenta`); }
export async function getAssets(): Promise<Asset[]> { return request("/api/market/assets"); }
export async function getHistory(symbol: string): Promise<HistoryPoint[]> { return request(`/api/market/assets/${encodeURIComponent(symbol)}/history`); }
export async function getDolarQuotes(): Promise<DolarQuotes> { return request("/api/market/dolar"); }
export async function getBalance(): Promise<{ ars: number; usd: number }> { return request("/api/account/balance"); }
export async function createMovimiento(movimiento: CreateMovimientoRequest): Promise<{ id: number }> {
  return request("/api/movimientos/", { method: "POST", body: JSON.stringify(movimiento) });
}
export async function getPlazos(): Promise<Array<{ label: string; detalle: string; ars: number; usd: number }>> { return request("/api/cuenta/plazos"); }
export async function getOrdenesPendientes(): Promise<Array<{ desc: string; ars: number; usd: number }>> { return request("/api/ordenes/pendientes"); }
export async function getPortfolio(): Promise<Holding[]> { return request("/api/portfolio"); }
export async function placeOrder(order: Order): Promise<{ ok: boolean; id: string }> { return request("/api/orders", { method: "POST", body: JSON.stringify(order) }); }
export async function getGroups(): Promise<Group[]> { return request("/api/grupos"); }
export async function createGroup(nombre: string, password: string): Promise<Group> { return request("/api/grupos", { method: "POST", body: JSON.stringify({ nombre, password }) }); }
export async function joinGroup(nombre: string, password: string): Promise<Group> { return request("/api/grupos/unirse", { method: "POST", body: JSON.stringify({ nombre, password }) }); }
export async function contributeToGroup(groupId: string, monto: number, moneda: Moneda = "ARS"): Promise<Group> {
  return request(`/api/grupos/${groupId}/aportes`, {
    method: "POST",
    body: JSON.stringify({ monto, moneda }),
  });
}
export async function groupBuy(groupId: string, ticker: string, cantidad: number): Promise<Group> { return request(`/api/grupos/${groupId}/operaciones`, { method: "POST", body: JSON.stringify({ ticker, cantidad }) }); }
