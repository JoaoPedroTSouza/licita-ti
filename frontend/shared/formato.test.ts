import { describe, expect, it } from "vitest";
import { ETAPAS, formatarAproxBrl, formatarDinheiro, formatarPrazo } from "./formato";

describe("formatarDinheiro", () => {
  it("formata BRL e USD", () => {
    expect(formatarDinheiro({ valor: "120000.00", moeda: "BRL" })).toBe("R$ 120.000,00");
    expect(formatarDinheiro({ valor: "40000", moeda: "USD" })).toBe("US$ 40.000,00");
  });
  it("devolve traço quando não há valor", () => {
    expect(formatarDinheiro(null)).toBe("—");
  });
  it("usa o código para outras moedas", () => {
    expect(formatarDinheiro({ valor: "1500.5", moeda: "EUR" })).toBe("EUR 1.500,50");
  });
});

describe("formatarAproxBrl", () => {
  it("milhares viram mil, arredondados", () => {
    expect(formatarAproxBrl("216000.00")).toBe("≈ R$ 216 mil");
    expect(formatarAproxBrl("215600")).toBe("≈ R$ 216 mil");
  });
  it("milhões têm uma casa decimal", () => {
    expect(formatarAproxBrl("1234567")).toBe("≈ R$ 1,2 mi");
  });
  it("abaixo de mil mostra o valor inteiro", () => {
    expect(formatarAproxBrl("850.40")).toBe("≈ R$ 850");
  });
  it("null vira texto vazio", () => {
    expect(formatarAproxBrl(null)).toBe("");
  });
});

describe("formatarPrazo", () => {
  // 2026-10-23 12:00 em Brasília (UTC-3)
  const agora = new Date("2026-10-23T15:00:00Z");

  it("sem prazo devolve traço", () => {
    expect(formatarPrazo(null, agora)).toBe("—");
  });
  it("hoje mostra a hora de Brasília", () => {
    expect(formatarPrazo("2026-10-23T21:00:00-03:00", agora)).toBe("hoje 21:00");
  });
  it("prazo em UTC que cai hoje no horário de Brasília", () => {
    // 2026-10-24T01:30Z = 22:30 de 23/10 em Brasília
    expect(formatarPrazo("2026-10-24T01:30:00Z", agora)).toBe("hoje 22:30");
  });
  it("prazo em UTC já no dia seguinte em Brasília é amanhã", () => {
    // 2026-10-24T03:00Z = 00:00 de 24/10 em Brasília
    expect(formatarPrazo("2026-10-24T03:00:00Z", agora)).toBe("amanhã");
  });
  it("de 2 a 6 dias usa 'em N dias'", () => {
    expect(formatarPrazo("2026-10-25T15:00:00Z", agora)).toBe("em 2 dias");
    expect(formatarPrazo("2026-10-28T15:00:00Z", agora)).toBe("em 5 dias");
    expect(formatarPrazo("2026-10-29T15:00:00Z", agora)).toBe("em 6 dias");
  });
  it("a partir de 7 dias usa dia/mês", () => {
    expect(formatarPrazo("2026-10-30T15:00:00Z", agora)).toBe("30/out");
    expect(formatarPrazo("2026-11-12T15:00:00Z", agora)).toBe("12/nov");
  });
  it("vencido quando o prazo já passou", () => {
    expect(formatarPrazo("2026-10-23T14:59:00Z", agora)).toBe("vencido");
    expect(formatarPrazo("2026-10-20T10:00:00Z", agora)).toBe("vencido");
  });
  it("não depende do fuso da máquina: 'agora' tarde da noite em UTC ainda é o mesmo dia em Brasília", () => {
    const tarde = new Date("2026-10-24T01:00:00Z"); // 22:00 de 23/10 em Brasília
    expect(formatarPrazo("2026-10-24T02:00:00Z", tarde)).toBe("hoje 23:00");
    expect(formatarPrazo("2026-10-24T12:00:00Z", tarde)).toBe("amanhã");
  });
});

describe("ETAPAS", () => {
  it("segue a ordem do funil", () => {
    expect(ETAPAS.map((e) => e.id)).toEqual([
      "analisando", "proposta_enviada", "negociacao", "fechado", "perdido",
    ]);
    expect(ETAPAS.map((e) => e.rotulo)).toEqual([
      "Analisando", "Proposta enviada", "Negociação", "Fechado", "Perdido",
    ]);
  });
});
