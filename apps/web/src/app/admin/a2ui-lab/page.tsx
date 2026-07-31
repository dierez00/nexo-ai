import type { Metadata } from "next";

import { A2UILab } from "./lab-page";

export const metadata: Metadata = {
  title: "Banco A2UI — Nexo AI",
  description:
    "Renderer del catálogo ciudadano A2UI y medición del tiempo hasta la primera superficie.",
};

export default function Page() {
  return <A2UILab />;
}
