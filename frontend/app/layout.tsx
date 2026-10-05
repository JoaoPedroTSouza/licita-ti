import type { Metadata, Viewport } from "next";
import "./globals.css";
import RegistrarSW from "@/components/RegistrarSW";

export const metadata: Metadata = {
  title: "Licita TI",
  description: "Editais de desenvolvimento web e consultoria de TI",
  applicationName: "Licita TI",
  icons: { icon: "/icons/icon-192.png", apple: "/icons/icon-192.png" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#0f766e" },
    { media: "(prefers-color-scheme: dark)", color: "#0e1413" },
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
