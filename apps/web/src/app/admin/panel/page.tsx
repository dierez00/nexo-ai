import type { Metadata } from "next";

import { AdminPanelPage } from "./panel-page";

export const metadata: Metadata = {
  title: "Panel admin — Nexo AI",
  description: "Métricas por dominio generadas desde las superficies A2UI.",
};

export default function Page() {
  return <AdminPanelPage />;
}
