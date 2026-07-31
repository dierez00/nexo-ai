import type { Metadata } from "next";
import { RunsPage } from "./runs-page";

export const metadata: Metadata = {
  title: "Runs del agente — Nexo AI",
  description: "Ejecuciones del agente con dominio, canal, estado y trace id.",
  openGraph: {
    title: "Runs del agente — Nexo AI",
    description: "Tabla filtrable de ejecuciones con detalle por run.",
  },
};

export default function Page() {
  return <RunsPage />;
}
