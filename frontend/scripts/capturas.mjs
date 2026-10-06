// Gera capturas de tela do app (desktop 1440px e celular, tema claro e escuro).
// Uso no CI: API em :8000 com dados de demonstração e PWA em :3000.
import { mkdirSync } from "node:fs";
import { chromium } from "playwright";

const WEB = process.env.WEB_URL ?? "http://localhost:3000";
const API = process.env.API_URL ?? "http://localhost:8000";
const SAIDA = process.env.SAIDA ?? "capturas";
mkdirSync(SAIDA, { recursive: true });

const { token } = await (
  await fetch(`${API}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ senha: process.env.SENHA ?? "demo" }),
  })
).json();

const editais = await (await fetch(`${API}/api/editais?filtro=todos&por_pagina=1`, { headers: { Authorization: `Bearer ${token}` } })).json();
const primeiro = editais.itens[0]?.id ?? 1;

const PAGINAS = [
  ["painel", "/"],
  ["editais", "/editais"],
  ["edital", `/editais/${primeiro}`],
  ["ideias", "/ideias"],
  ["ideia-editor", "/ideias?nova=1"],
  ["acompanhamento", "/acompanhamento"],
  ["ajustes", "/ajustes"],
];

const PERFIS = [
  { nome: "desktop", viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1, tema: "light" },
  { nome: "desktop-escuro", viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1, tema: "dark", so: ["painel", "ideias", "edital"] },
  { nome: "tablet", viewport: { width: 1024, height: 768 }, deviceScaleFactor: 1, tema: "light", so: ["painel", "ideias"] },
  { nome: "celular", viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, tema: "light", isMobile: true, hasTouch: true },
];

const browser = await chromium.launch();
for (const perfil of PERFIS) {
  const ctx = await browser.newContext({
    viewport: perfil.viewport,
    deviceScaleFactor: perfil.deviceScaleFactor,
    colorScheme: perfil.tema,
    isMobile: perfil.isMobile ?? false,
    hasTouch: perfil.hasTouch ?? false,
    locale: "pt-BR",
    timezoneId: "America/Sao_Paulo",
    serviceWorkers: "block",
  });
  await ctx.addInitScript((t) => localStorage.setItem("licita_token", t), token);
  const page = await ctx.newPage();
  page.on("pageerror", (e) => console.error(`[${perfil.nome}] erro na página:`, e.message));

  for (const [nome, rota] of PAGINAS) {
    if (perfil.so && !perfil.so.includes(nome)) continue;
    await page.goto(`${WEB}${rota}`, { waitUntil: "networkidle" });
    await page.waitForTimeout(600);
    const arquivo = `${SAIDA}/${perfil.nome}-${nome}.png`;
    await page.screenshot({ path: arquivo, fullPage: nome !== "ideia-editor" });
    console.log("ok", arquivo);
  }

  // Tooltip da régua de prazos
  if (perfil.nome === "desktop") {
    await page.goto(`${WEB}/`, { waitUntil: "networkidle" });
    const chip = page.locator("ol li a").first();
    if (await chip.count()) {
      await chip.hover();
      await page.waitForTimeout(200);
      await page.screenshot({ path: `${SAIDA}/desktop-painel-tooltip.png`, clip: { x: 240, y: 0, width: 1200, height: 620 } });
    }
  }
  await ctx.close();
}

// Tela de login
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const p = await ctx.newPage();
await p.goto(`${WEB}/login`, { waitUntil: "networkidle" });
await p.screenshot({ path: `${SAIDA}/desktop-login.png` });
await browser.close();
