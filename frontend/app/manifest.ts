import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    id: "/",
    name: "Licita TI — editais de tecnologia",
    short_name: "Licita TI",
    description: "Monitoramento de editais de desenvolvimento web e consultoria de TI no PNCP.",
    start_url: "/?origem=pwa",
    scope: "/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#0e1413",
    theme_color: "#0f766e",
    lang: "pt-BR",
    categories: ["business", "productivity"],
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      { src: "/icons/maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
    shortcuts: [
      { name: "Acompanhamento", url: "/acompanhamento", icons: [{ src: "/icons/icon-192.png", sizes: "192x192" }] },
    ],
  };
}
