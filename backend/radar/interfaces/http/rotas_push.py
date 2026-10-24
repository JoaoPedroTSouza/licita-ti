"""Rotas de Web Push: chave pública, inscrição do aparelho e notificação de teste."""
from fastapi import APIRouter, Depends, Header, Response, status

from radar.container import Container
from radar.interfaces.http.auth import obter_container
from radar.interfaces.http.dtos import ChavePublicaDTO, EntreguesDTO, InscricaoPushIn

router = APIRouter(prefix="/push")


@router.get("/chave-publica", response_model=ChavePublicaDTO)
def chave_publica(c: Container = Depends(obter_container)):
    return ChavePublicaDTO(chave=c.settings.vapid_public_key)


@router.post("/inscrever", status_code=status.HTTP_204_NO_CONTENT)
def inscrever(
    corpo: InscricaoPushIn, user_agent: str | None = Header(default=None),
    c: Container = Depends(obter_container),
):
    c.notificador.inscrever(corpo.endpoint, corpo.keys.p256dh, corpo.keys.auth, user_agent)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/teste", response_model=EntreguesDTO)
def testar(c: Container = Depends(obter_container)):
    n = c.notificador.enviar("Radar", "Notificação de teste", f"{c.settings.app_url}/ajustes")
    return EntreguesDTO(entregues=n)
