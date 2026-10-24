import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    id: "/",
    name: "Radar",
    short_name: "Radar",
    description: "Oportunidades remotas, funil e lembretes",
    start_url: "/hoje?origem=pwa",
    scope: "/",
    display: "standalone",
    orientation: "any",
    background_color: "#f7f7f5",
    theme_color: "#2f5d50",
    lang: "pt-BR",
    categories: ["business", "productivity"],
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      { src: "/icons/maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
    shortcuts: [
      { name: "Hoje", url: "/hoje", icons: [{ src: "/icons/icon-192.png", sizes: "192x192" }] },
      { name: "Entrada", url: "/entrada", icons: [{ src: "/icons/icon-192.png", sizes: "192x192" }] },
    ],
  };
}
