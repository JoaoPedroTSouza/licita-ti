import pytest

from radar.domain.erros import NaoEncontrado
from radar.infrastructure.arquivos.disco import ArmazenamentoEmDisco


def test_disco_salva_e_abre_sem_usar_nome_original(tmp_path):
    raiz = tmp_path / "ainda" / "nao" / "existe"
    arm = ArmazenamentoEmDisco(raiz)
    chave = arm.salvar("../../contrato final.pdf", b"conteudo")
    assert len(chave) == 32 and int(chave, 16) >= 0
    assert arm.abrir(chave) == b"conteudo"
    arquivos = [p for p in raiz.rglob("*") if p.is_file()]
    assert len(arquivos) == 1 and "contrato" not in arquivos[0].name
    assert raiz in arquivos[0].parents


@pytest.mark.parametrize("chave", ["../segredo", "nao-existe", "a" * 32, "", "A" * 32, "a" * 31 + "/"])
def test_disco_rejeita_chave_desconhecida_ou_malformada(tmp_path, chave):
    arm = ArmazenamentoEmDisco(tmp_path)
    with pytest.raises(NaoEncontrado):
        arm.abrir(chave)
