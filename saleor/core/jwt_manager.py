import json
import logging
from os.path import exists

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.conf import settings
from jwt.algorithms import RSAAlgorithm

logger = logging.getLogger(__name__)


class JWTManager:
    KEY_FILE_FOR_DEBUG = ".jwt_key.pem"

    @classmethod
    def get_private_key(cls, *_args, **_kwargs):
        pem = settings.RSA_PRIVATE_KEY
        if not pem and settings.DEBUG:
            logger.warning(
                "RSA_PRIVATE_KEY is missing. Using temporary key for local development."
            )
            return cls.load_debug_private_key()
        if isinstance(pem, str):
            pem = pem.encode("utf-8")
        return serialization.load_pem_private_key(
            pem, password=None
        )  # TODO Add password env

    @classmethod
    def load_debug_private_key(cls):
        key_path = f"{settings.PROJECT_ROOT}/{cls.KEY_FILE_FOR_DEBUG}"
        if exists(key_path):
            return cls._load_local_private_key(key_path)

        return cls._create_local_private_key(key_path)

    @classmethod
    def _load_local_private_key(cls, path) -> "rsa.RSAPrivateKey":
        with open(path, "rb") as key_file:
            return serialization.load_pem_private_key(
                key_file.read(), password=None
            )  # type: ignore

    @classmethod
    def _create_local_private_key(cls, path) -> "rsa.RSAPrivateKey":
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        with open(path, "wb") as p_key_file:
            p_key_file.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
        return private_key

    @classmethod
    def get_public_key(cls, *_args, **_kwargs):
        private_key = cls.get_private_key()
        return private_key.public_key()

    @classmethod
    def get_jwk(cls) -> dict:
        jwk_dict = json.loads(RSAAlgorithm.to_jwk(cls.get_public_key()))
        jwk_dict.update({"use": "sig", "kid": "1"})
        return jwk_dict

    @classmethod
    def encode(cls, payload):
        return jwt.encode(
            payload, cls.get_private_key(), algorithm="RS256", headers={"kid": "1"}
        )

    @classmethod
    def decode(cls, token, verify_expiration: bool = True):
        headers = jwt.get_unverified_header(token)
        if headers.get("alg") == "HS256":
            return jwt.decode(
                token,
                settings.SECRET_KEY,  # type: ignore
                algorithms=["HS256"],
                options={"verify_exp": verify_expiration},
            )
        return jwt.decode(
            token,
            cls.get_public_key(),
            algorithms=["RS256"],
            options={"verify_exp": verify_expiration},
        )
