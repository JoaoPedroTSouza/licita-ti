import type { Metadata, Viewport } from "next";
import "./globals.css";
import RegistrarSW from "@/shared/pwa/RegistrarSW";

export const metadata: Metadata = {
  title: "Radar",
  description: "Oportunidades remotas, funil e lembretes",
  applicationName: "Radar",
  icons: { icon: "/icons/icon-192.png", apple: "/icons/icon-192.png" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f7f7f5" },
    { media: "(prefers-color-scheme: dark)", color: "#121413" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="min-h-dvh font-sans antialiased">
        <RegistrarSW />
        {children}
      </body>
    </html>
  );
}
