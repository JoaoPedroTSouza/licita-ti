import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    id: "/",
    name: "Licita TI — editais de tecnologia",
    short_name: "Licita TI",
    description: "Editais de TI do PNCP, prazos e cadastro de ideias.",
    start_url: "/?origem=pwa",
    scope: "/",
    display: "standalone",
    orientation: "any",
    background_color: "#f6f7fb",
    theme_color: "#3d63dd",
    lang: "pt-BR",
    categories: ["business", "productivity"],
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      { src: "/icons/maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
    shortcuts: [
      { name: "Editais", url: "/editais", icons: [{ src: "/icons/icon-192.png", sizes: "192x192" }] },
      { name: "Nova ideia", url: "/ideias?nova=1", icons: [{ src: "/icons/icon-192.png", sizes: "192x192" }] },
    ],
  };
}
