import type { Metadata } from "next";
import fixture from "../../../../public/fixtures/workflow/success.json";
import { WorkflowReplayView } from "@/features/workflow/WorkflowReplayView";
import type { WorkflowReplay } from "@/features/workflow/types";

export const metadata: Metadata = {
  title: "Workflow del agente — Nexo AI",
  description: "Grafo y línea de tiempo reconstruidos desde eventos de ejecución.",
  openGraph: {
    title: "Workflow del agente — Nexo AI",
    description: "Replay verificable de una solicitud entre agentes y herramientas.",
  },
};

export default function Page() {
  return <WorkflowReplayView replay={fixture.replay as WorkflowReplay} />;
}
