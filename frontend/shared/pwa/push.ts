import { push } from "../api/cliente";
import type { InscricaoPush } from "../api/tipos";

function base64UrlParaUint8(base64: string): Uint8Array<ArrayBuffer> {
  const padding = "=".repeat((4 - (base64.length % 4)) % 4);
  const b64 = (base64 + padding).replace(/-/g, "+").replace(/_/g, "/");
  const bruto = atob(b64);
  const saida = new Uint8Array(new ArrayBuffer(bruto.length));
  for (let i = 0; i < bruto.length; i++) saida[i] = bruto.charCodeAt(i);
  return saida;
}

export function pushSuportado(): boolean {
  return typeof window !== "undefined" && "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
}

export async function inscricaoAtual(): Promise<PushSubscription | null> {
  if (!pushSuportado()) return null;
  const reg = await navigator.serviceWorker.ready;
  return reg.pushManager.getSubscription();
}

/** Deve ser chamada a partir de um toque do usuário (exigência do navegador). */
export async function ativarPush(): Promise<void> {
  if (!pushSuportado()) throw new Error("Este navegador não suporta notificações push.");
  const permissao = await Notification.requestPermission();
  if (permissao !== "granted") throw new Error("Permissão de notificação negada. Libere nas configurações do navegador.");

  const reg = await navigator.serviceWorker.ready;
  const { chave } = await push.chavePublica();
  let sub = await reg.pushManager.getSubscription();
  if (!sub) {
    sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: base64UrlParaUint8(chave),
    });
  }
  await push.inscrever(sub.toJSON() as InscricaoPush);
}

/** Cancela a inscrição neste aparelho; o servidor descarta endpoints expirados sozinho. */
export async function desativarPush(): Promise<void> {
  const sub = await inscricaoAtual();
  if (sub) await sub.unsubscribe();
}
