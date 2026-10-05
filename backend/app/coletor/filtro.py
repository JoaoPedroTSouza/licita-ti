"""Primeiro corte barato: pontuação por palavras-chave (sem acento, sem caixa, com limite de palavra)."""

import re
import unicodedata
from functools import lru_cache


def normalizar_texto(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto or "")
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acento.lower()).strip()


@lru_cache(maxsize=2048)
def _padrao(termo: str) -> re.Pattern:
    t = re.escape(normalizar_texto(termo)).replace(r"\ ", r"\s+")
    # aceita plural simples no fim do termo ("sistema" → "sistemas", "aplicativo" → "aplicativos")
    return re.compile(rf"(?<![a-z0-9]){t}(?:s|es)?(?![a-z0-9])")


def pontuar(texto: str, prefs: dict) -> tuple[int, list[str], bool]:
    """Retorna (score, termos encontrados, excluido)."""
    t = normalizar_texto(texto)
    encontrados: list[str] = []
    score = 0
    for termo in prefs.get("palavras_chave", []):
        if _padrao(termo).search(t):
            encontrados.append(termo)
            score += 2
    for termo in prefs.get("palavras_reforco", []):
        if _padrao(termo).search(t):
            encontrados.append(termo)
            score += 1
    excluido = any(_padrao(x).search(t) for x in prefs.get("palavras_exclusao", []))
    return score, encontrados, excluido


def passa_filtros_basicos(dados: dict, prefs: dict) -> bool:
    ufs = [u.upper() for u in prefs.get("ufs") or []]
    if ufs and (dados.get("uf") or "").upper() not in ufs:
        return False
    valor = dados.get("valor_estimado") or 0
    vmin = prefs.get("valor_minimo") or 0
    vmax = prefs.get("valor_maximo") or 0
    if vmin and valor and valor < vmin:
        return False
    if vmax and valor and valor > vmax:
        return False
    return True


def eh_candidato(dados: dict, prefs: dict) -> tuple[bool, int, list[str]]:
    texto = f"{dados.get('objeto', '')} {dados.get('informacao_complementar') or ''}"
    score, termos, excluido = pontuar(texto, prefs)
    ok = (
        not excluido
        and score >= int(prefs.get("score_minimo_keywords", 2))
        and passa_filtros_basicos(dados, prefs)
    )
    return ok, score, termos
