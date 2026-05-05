import type { Metadata } from "next";
import { Public_Sans, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { GlobalChatBubble } from "@/components/chat/GlobalChatBubble";

const publicSans = Public_Sans({
  variable: "--font-public-sans",
  subsets: ["latin"],
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "ECOS — Observatorio de Riesgo Epidemiológico | Colombia",
  description:
    "Plataforma nacional de alerta temprana para dengue, malaria, zika y chikungunya en Colombia. IA predictiva + datos abiertos + NLP para anticipar brotes 2–4 semanas antes del reporte oficial.",
  keywords: [
    "epidemiología",
    "dengue",
    "malaria",
    "Colombia",
    "alerta temprana",
    "vigilancia epidemiológica",
    "SIVIGILA",
    "datos abiertos",
  ],
  authors: [{ name: "Equipo ECOS" }],
  openGraph: {
    title: "ECOS — Observatorio de Riesgo Epidemiológico",
    description: "IA predictiva para anticipar brotes epidemiológicos en Colombia.",
    type: "website",
    locale: "es_CO",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="es"
      className={`${publicSans.variable} ${spaceGrotesk.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col font-sans bg-(--color-background) text-(--color-primary)">
        <Navbar />
        <main className="flex-1 flex flex-col">
          {children}
        </main>
        <Footer />
        <GlobalChatBubble />
      </body>
    </html>
  );
}
