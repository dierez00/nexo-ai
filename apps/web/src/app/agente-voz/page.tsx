import type { Metadata } from "next";

import VoiceAgent from "@/features/voice-agent/VoiceAgent";

export const metadata: Metadata = {
  title: "Agente de voz — Nexo AI",
  description: "Resuelve tu trámite hablando: transcripción en vivo y estado de la llamada.",
  openGraph: {
    title: "Agente de voz — Nexo AI",
    description: "Llamada guiada con el agente institucional de Nexo AI.",
  },
};

export default function AgenteVozPage() {
  return <VoiceAgent />;
}
