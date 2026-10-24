"""Armazenamento de arquivos em disco; o nome original nunca entra no caminho."""
import re
from pathlib import Path
from uuid import uuid4

from radar.domain.erros import NaoEncontrado

_CHAVE = re.compile(r"[0-9a-f]{32}")


class ArmazenamentoEmDisco:
    def __init__(self, raiz: Path) -> None:
        self._raiz = Path(raiz)

    def salvar(self, nome: str, conteudo: bytes) -> str:
        self._raiz.mkdir(parents=True, exist_ok=True)
        chave = uuid4().hex
        (self._raiz / chave).write_bytes(conteudo)
        return chave

    def abrir(self, chave: str) -> bytes:
        if not _CHAVE.fullmatch(chave):
            raise NaoEncontrado("Arquivo não encontrado")
        caminho = self._raiz / chave
        if not caminho.is_file():
            raise NaoEncontrado("Arquivo não encontrado")
        return caminho.read_bytes()
