"""Regras de dependência entre camadas: domínio puro, aplicação só enxerga o domínio."""
import ast
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent / "radar"

PROIBIDOS_NO_DOMINIO = ("fastapi", "sqlalchemy", "httpx", "anthropic", "pywebpush", "radar.application", "radar.infrastructure", "radar.interfaces")
PROIBIDOS_NA_APLICACAO = PROIBIDOS_NO_DOMINIO[:5] + ("radar.infrastructure", "radar.interfaces")


def _imports(arquivo: Path) -> set[str]:
    nomes: set[str] = set()
    for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
        if isinstance(no, ast.Import):
            nomes.update(a.name for a in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module and no.level == 0:
            nomes.add(no.module)
            nomes.update(f"{no.module}.{a.name}" for a in no.names)
    return nomes


def _violacoes(camada: str, proibidos: tuple[str, ...]) -> list[str]:
    pasta = RAIZ / camada
    assert pasta.is_dir(), f"camada ausente: {pasta}"
    achados = []
    for arquivo in sorted(pasta.rglob("*.py")):
        for nome in _imports(arquivo):
            if any(nome == p or nome.startswith(p + ".") for p in proibidos):
                achados.append(f"{arquivo.relative_to(RAIZ)} importa {nome}")
    return achados


def test_dominio_nao_depende_de_frameworks_nem_de_outras_camadas():
    assert _violacoes("domain", PROIBIDOS_NO_DOMINIO) == []


def test_aplicacao_depende_so_do_dominio():
    assert _violacoes("application", PROIBIDOS_NA_APLICACAO) == []
