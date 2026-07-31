import type { Metadata } from "next";
import { Suspense } from "react";
import { SeguimientoPage } from "./seguimiento-page";

export const metadata: Metadata = {
  title: "Seguimiento del trámite — Nexo AI",
  description:
    "Sigue tu folio paso a paso: qué pasó, quién lo informó y cuál es la siguiente acción.",
  openGraph: {
    title: "Seguimiento del trámite — Nexo AI",
    description: "Línea de tiempo con trazabilidad de estado, fuente y acción.",
  },
};

export default function Page() {
  return (
    <Suspense fallback={null}>
      <SeguimientoPage />
    </Suspense>
  );
}
