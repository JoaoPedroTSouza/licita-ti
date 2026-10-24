"use client";

import { useEffect } from "react";

export default function RegistrarSW() {
  useEffect(() => {
    if (!("serviceWorker" in navigator)) return;
    navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch((e) => console.warn("SW não registrado", e));
  }, []);
  return null;
}
