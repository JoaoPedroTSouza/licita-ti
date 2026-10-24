# ReliefWeb (nao implementada)

Status: inviavel sem um `appname` aprovado. Fonte nao registrada; o adaptador nao foi escrito.

## Evidencia (2026-10-23)

Requisicao com `appname` arbitrario, User-Agent identificado:

    GET https://api.reliefweb.int/v2/jobs?appname=radar&limit=1
    -> HTTP 403
    {"status":403,"time":23,"error":{"type":"AccessDeniedHttpException",
     "message":"You are not using an approved appname. Kindly request an appname from ReliefWeb
     here: https://apidoc.reliefweb.int/parameters#appname"}}

A API v2 exige um `appname` pre-aprovado pela ReliefWeb (solicitacao em
https://apidoc.reliefweb.int/parameters#appname). O dono nao tem um.

## Para ativar depois

1. Solicitar o appname no link acima.
2. Definir `RELIEFWEB_APPNAME` no `.env` (`Settings.reliefweb_appname`, ja existe, vazio por padrao).
3. Implementar `FonteReliefWeb(http, appname)` em `radar/infrastructure/fontes/reliefweb.py`:
   `GET https://api.reliefweb.int/v2/jobs`, filtro `type: Consultancy`, categoria
   `Information and Communications Technology`, `date.created >= desde`, campos
   `title, body, source, country, date.closing, url, language`.
