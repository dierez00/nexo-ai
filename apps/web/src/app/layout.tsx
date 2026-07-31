import type { Metadata } from "next";
import { Inter, IBM_Plex_Mono } from "next/font/google";
import { Providers } from "@/components/providers";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  weight: ["400", "500", "600", "700", "800"],
});

const ibmPlexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "Nexo AI — Trámites institucionales sin filas",
  description:
    "Nexo AI acompaña a la ciudadanía en trámites de vehículos, empresas, registro civil, salud y ganadería por WhatsApp, voz o portal web.",
  authors: [{ name: "Nexo AI" }],
  icons: { icon: "/favicon.ico" },
  openGraph: {
    title: "Nexo AI — Trámites institucionales sin filas",
    description:
      "Portal ciudadano y panel interno para gestionar trámites con trazabilidad completa.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
  },
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
};

// ThemeToggle aplica la clase en un efecto, así que sin este script hay un flash
// claro antes de hidratar cuando la preferencia guardada es oscura.
const themeScript = `try{if(localStorage.getItem("nexo-theme")==="dark")document.documentElement.classList.add("dark")}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className={`${inter.variable} ${ibmPlexMono.variable}`}>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
