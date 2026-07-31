import type { Metadata } from "next";
import { TramitePage } from "./tramite-page";

export const metadata: Metadata = {
  title: "Detalle del trámite — Nexo AI",
  description:
    "Estado, requisitos, documentos, costos estimados y fuentes oficiales de tu trámite.",
  openGraph: {
    title: "Detalle del trámite — Nexo AI",
    description: "Todo tu expediente con la siguiente acción siempre visible.",
  },
};

export default function Page() {
  return <TramitePage />;
}
