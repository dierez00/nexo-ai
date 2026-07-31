import type { Metadata } from "next";

import { AdminShell } from "@/components/nexo/admin-shell";

export const metadata: Metadata = {
  title: "Panel admin — Nexo AI",
  description: "Métricas por dominio generadas desde las superficies A2UI.",
};

export default function Page() {
  // Vista en blanco a propósito: aquí irán las métricas por dominio generadas
  // desde A2UI.
  return <AdminShell title="Panel admin">{null}</AdminShell>;
}
