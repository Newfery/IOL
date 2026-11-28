import { Globe, Landmark, PieChart, Star, TrendingUp, type LucideIcon } from "lucide-react";
import type { Asset } from "./api";

export type Category = {
  slug: string;
  type: Asset["type"] | "Favoritos";
  label: string;
  desc: string;
  icon: LucideIcon;
  matches: (asset: Asset) => boolean;
};

export const CATEGORIES: Category[] = [
  {
    slug: "favoritos",
    type: "Favoritos",
    label: "Favoritos",
    desc: "Accedé rápido a los activos que más te interesan.",
    icon: Star,
    matches: () => true,
  },
  {
    slug: "acciones",
    type: "Acción",
    label: "Acciones Argentina",
    desc: "Acciones de empresas argentinas cotizadas en BYMA.",
    icon: TrendingUp,
    matches: (asset) => asset.type === "Acción" && asset.currency === "ARS",
  },
  {
    slug: "cedears",
    type: "CEDEAR",
    label: "CEDEARs",
    desc: "Representaciones locales de activos extranjeros.",
    icon: Globe,
    matches: (asset) => asset.type === "CEDEAR",
  },
  {
    slug: "acciones-eeuu",
    type: "Acción",
    label: "Acciones EE.UU.",
    desc: "Acciones estadounidenses operadas en dólares.",
    icon: TrendingUp,
    matches: (asset) => asset.type === "Acción" && asset.currency === "USD",
  },
  {
    slug: "etfs",
    type: "ETF",
    label: "ETFs",
    desc: "Fondos cotizados de acciones, bonos y otros mercados.",
    icon: PieChart,
    matches: (asset) => asset.type === "ETF",
  },
  {
    slug: "bonos",
    type: "Bono",
    label: "Bonos",
    desc: "Títulos de deuda pública con pagos de interés periódicos.",
    icon: Landmark,
    matches: (asset) => asset.type === "Bono",
  },
];

export function findCategory(slug: string | undefined): Category | undefined {
  if (!slug) return undefined;
  return CATEGORIES.find((category) => category.slug === slug.toLowerCase());
}

export function categoryForAsset(asset: Asset): Category {
  return CATEGORIES.find((category) => category.type !== "Favoritos" && category.matches(asset))
    ?? CATEGORIES[1]!;
}
