"""Erros do domínio, traduzidos para HTTP apenas na camada de interface."""


class ErroDeDominio(Exception):
    """Base de todos os erros de regra de negócio."""


class NaoEncontrado(ErroDeDominio):
    """Entidade solicitada não existe."""


class TransicaoInvalida(ErroDeDominio):
    """Mudança de status não permitida pela regra."""
