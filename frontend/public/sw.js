/* Service worker do Licita TI: cache para uso offline + notificações push. */
const VERSAO = "v1";
const CACHE_SHELL = `shell-${VERSAO}`;
const CACHE_DADOS = `dados-${VERSAO}`;
const CACHE_ESTATICO = `estatico-${VERSAO}`;

const SHELL = ["/", "/acompanhamento", "/ajustes", "/login", "/manifest.webmanifest", "/icons/icon-192.png"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_SHELL).then((c) => Promise.allSettled(SHELL.map((u) => c.add(u))))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const validos = [CACHE_SHELL, CACHE_DADOS, CACHE_ESTATICO];
      for (const nome of await caches.keys()) {
        if (!validos.includes(nome)) await caches.delete(nome);
      }
      await self.clients.claim();
    })()
  );
});

async function redePrimeiro(req, cacheNome) {
  const cache = await caches.open(cacheNome);
  try {
    const resp = await fetch(req);
    if (resp.ok) cache.put(req, resp.clone());
    return resp;
  } catch (e) {
    const salvo = await cache.match(req);
    if (salvo) return salvo;
    throw e;
  }
}

async function cachePrimeiro(req) {
  const cache = await caches.open(CACHE_ESTATICO);
  const salvo = await cache.match(req);
  if (salvo) return salvo;
  const resp = await fetch(req);
  if (resp.ok) cache.put(req, resp.clone());
  return resp;
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // Arquivos versionados do Next: imutáveis
  if (url.pathname.startsWith("/_next/static/") || url.pathname.startsWith("/icons/")) {
    event.respondWith(cachePrimeiro(req));
    return;
  }

  // Dados da API: tenta a rede; offline, mostra o último resultado
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(redePrimeiro(req, CACHE_DADOS));
    return;
  }

  // Páginas: rede primeiro; offline cai no cache ou na página inicial
  if (req.mode === "navigate") {
    event.respondWith(
      redePrimeiro(req, CACHE_SHELL).catch(async () => (await caches.match("/")) || Response.error())
    );
  }
});

self.addEventListener("push", (event) => {
  let dados = {};
  try {
    dados = event.data ? event.data.json() : {};
  } catch {
    dados = { body: event.data ? event.data.text() : "" };
  }
  const titulo = dados.title || "Licita TI";
  event.waitUntil(
    self.registration.showNotification(titulo, {
      body: dados.body || "",
      icon: "/icons/icon-192.png",
      badge: "/icons/badge-96.png",
      tag: dados.tag || undefined,
      renotify: Boolean(dados.tag),
      vibrate: [80, 40, 80],
      data: { url: dados.url || "/" },
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const destino = new URL(event.notification.data?.url || "/", self.location.origin).href;
  event.waitUntil(
    (async () => {
      const abertas = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
      for (const c of abertas) {
        if ("focus" in c) {
          await c.focus();
          if ("navigate" in c) return c.navigate(destino);
          return;
        }
      }
      return self.clients.openWindow(destino);
    })()
  );
});
