"""Regra rígida de admissão: decide se uma oportunidade classificada é descartada."""
from datetime import datetime

from radar.domain.oportunidade import Classificacao, Modalidade, MotivoDescarteAuto

IDIOMAS_ACEITOS = frozenset({"pt", "en"})


def avaliar_admissao(
    c: Classificacao, prazo: datetime | None, agora: datetime
) -> MotivoDescarteAuto | None:
    if c.modalidade != Modalidade.REMOTO_TOTAL:
        return MotivoDescarteAuto.NAO_REMOTA
    if c.idioma not in IDIOMAS_ACEITOS:
        return MotivoDescarteAuto.IDIOMA
    if prazo is not None and prazo < agora:
        return MotivoDescarteAuto.PRAZO_VENCIDO
    if not c.relevante:
        return MotivoDescarteAuto.IRRELEVANTE
    return None
