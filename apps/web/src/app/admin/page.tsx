import type { Metadata } from "next";
import { AdminDashboard } from "./dashboard-page";

export const metadata: Metadata = {
  title: "Dashboard de operaciones — Nexo AI",
  description: "Volumen de trámites, tiempo promedio de resolución y tasa de éxito.",
  openGraph: {
    title: "Dashboard de operaciones — Nexo AI",
    description: "Métricas y tendencia de la operación de Nexo AI.",
  },
};

export default function Page() {
  return <AdminDashboard />;
}
