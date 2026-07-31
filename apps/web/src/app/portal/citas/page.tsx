import type { Metadata } from "next";
import { Suspense } from "react";
import { CitasPage } from "./citas-page";

export const metadata: Metadata = {
  title: "Reservar cita — Nexo AI",
  description: "Elige fecha y hora disponibles y confirma tu cita presencial.",
  openGraph: {
    title: "Reservar cita — Nexo AI",
    description: "Slots disponibles, resumen claro y confirmación explícita.",
  },
};

export default function Page() {
  return (
    <Suspense fallback={null}>
      <CitasPage />
    </Suspense>
  );
}
