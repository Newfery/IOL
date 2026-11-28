import { useState } from "react";
import { X } from "lucide-react";
import { placeOrder, type Asset } from "@/lib/api";

const fmt = (value: number, asset: Asset) =>
  value.toLocaleString("es-AR", {
    style: "currency",
    currency: asset.currency,
    maximumFractionDigits: 2,
  });

export function OrderDialog({ asset, onClose }: { asset: Asset; onClose: () => void }) {
  const [side, setSide] = useState<"buy" | "sell">("buy");
  const [qtyText, setQtyText] = useState("1");
  const qty = Math.max(0, Math.floor(Number(qtyText) || 0));
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function submit() {
    if (qty < 1) {
      setError("Ingresá una cantidad válida.");
      return;
    }

    setSubmitting(true);
    setError("");
    setMessage("");
    try {
      await placeOrder({ symbol: asset.symbol, side, qty, price: asset.price });
      setMessage(`Orden ejecutada (${side === "buy" ? "compra" : "venta"} ${qty} ${asset.symbol}).`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo ejecutar la orden.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="order-dialog-title"
        className="w-full max-w-md rounded-xl border border-border bg-card p-6"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between">
          <div>
            <h2 id="order-dialog-title" className="font-display text-lg font-semibold">Operar {asset.symbol}</h2>
            <p className="text-sm text-muted-foreground">{asset.name} · {fmt(asset.price, asset)}</p>
          </div>
          <button onClick={onClose} aria-label="Cerrar" className="text-muted-foreground hover:text-foreground">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="mt-4 grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => setSide("buy")}
            className={`rounded-md py-2 text-sm font-semibold ${side === "buy" ? "bg-gain text-background" : "bg-muted"}`}
          >
            Comprar
          </button>
          <button
            type="button"
            onClick={() => setSide("sell")}
            className={`rounded-md py-2 text-sm font-semibold ${side === "sell" ? "bg-loss text-background" : "bg-muted"}`}
          >
            Vender
          </button>
        </div>
        <label htmlFor="order-quantity" className="mt-4 block text-xs text-muted-foreground">Cantidad</label>
        <input
          id="order-quantity"
          type="number"
          min={1}
          step={1}
          value={qtyText}
          disabled={submitting}
          onChange={(event) => setQtyText(event.target.value)}
          className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2"
        />
        <div className="mt-3 flex justify-between text-sm">
          <span className="text-muted-foreground">Total estimado</span>
          <span className="font-mono">{fmt(asset.price * qty, asset)}</span>
        </div>
        <button
          type="button"
          onClick={submit}
          disabled={submitting}
          className="mt-4 w-full rounded-md bg-primary py-2 font-semibold text-primary-foreground disabled:opacity-60"
        >
          {submitting ? "Procesando..." : "Confirmar orden"}
        </button>
        {error && <p role="alert" className="mt-3 text-xs text-loss">{error}</p>}
        {message && <p role="status" className="mt-3 text-xs text-gain">{message}</p>}
      </div>
    </div>
  );
}
