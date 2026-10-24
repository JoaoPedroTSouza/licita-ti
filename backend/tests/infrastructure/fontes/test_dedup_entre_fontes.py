"""A mesma chamada vinda do UNGM e da OPAS gera a mesma chave de deduplicação."""
from datetime import date

from tests.infrastructure.fontes.test_ungm import BRASIL, ServidorUngm, _fonte as _fonte_ungm
from tests.infrastructure.fontes.test_opas import _fonte as _fonte_opas


def test_aviso_do_ungm_e_da_opas_tem_a_mesma_chave():
    avisos = _fonte_ungm(ServidorUngm(), [BRASIL]).buscar(date(2026, 10, 20))
    ungm = next(a for a in avisos if a.titulo.startswith("Estruturação do programa"))
    # UNGM: 20-Nov-2026 17:00 BRT (20:00 UTC), agência "UNDP"
    assert ungm.organizacao == "UNDP" and ungm.prazo.day == 20
    html = (
        '<article><div class="field--name-body">'
        f"<p><strong>{ungm.titulo.upper()}.</strong></p>"
        "<p>Prazo final para envio de propostas: 20/11/2026</p>"
        '<p><a href="https://www.ungm.org/Public/Notice/1">Clique aqui</a></p>'
        "</div></article>"
    ).encode()
    (opas,) = _fonte_opas(conteudo=html).buscar(date(2026, 10, 20))
    # OPAS: 20/11/2026 23:59 BRT cai em 21/11 UTC, e a organização é outra
    assert opas.organizacao == "OPAS/OMS Brasil" and opas.prazo.day == 21

    assert opas.chave_deduplicacao() == ungm.chave_deduplicacao()
