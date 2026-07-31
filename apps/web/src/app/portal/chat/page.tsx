import type { Metadata } from "next";
import { ChatPage } from "./chat-page";

export const metadata: Metadata = {
  title: "Chat de trámites — Nexo AI",
  description: "Inicia, agenda y da seguimiento a tus trámites conversando con el asistente.",
  openGraph: {
    title: "Chat de trámites — Nexo AI",
    description: "El chat es el centro de la app: sin pantallas fragmentadas.",
  },
};

export default function Page() {
  return <ChatPage />;
}
