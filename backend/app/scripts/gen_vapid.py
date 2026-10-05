"""Gera o par de chaves VAPID para o Web Push.

Uso: python -m app.scripts.gen_vapid
Copie as duas linhas exibidas para o arquivo .env.
"""

import base64

from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid01


def b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def main() -> None:
    v = Vapid01()
    v.generate_keys()
    priv = v.private_key.private_numbers().private_value.to_bytes(32, "big")
    pub = v.public_key.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    print(f"VAPID_PUBLIC_KEY={b64url(pub)}")
    print(f"VAPID_PRIVATE_KEY={b64url(priv)}")


if __name__ == "__main__":
    main()
