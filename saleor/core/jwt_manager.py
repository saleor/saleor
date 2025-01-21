import json
import logging
from functools import cache
from os.path import exists, join
from typing import cast

import jwt
from authlib.jose import JsonWebKey
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.color import color_style
from django.urls import reverse
from django.utils.module_loading import import_string
from jwt import api_jws, api_jwt
from jwt.algorithms import RSAAlgorithm

from .utils import build_absolute_uri, get_domain

logger = logging.getLogger(__name__)

PUBLIC_KEY: rsa.RSAPublicKey | None = None


class JWTManagerBase:
    @classmethod
    def get_domain(cls) -> str:
        return NotImplemented

    @classmethod
    def get_private_key(cls) -> rsa.RSAPrivateKey:
        return NotImplemented

    @classmethod
    def get_public_key(cls) -> rsa.RSAPublicKey:
        return NotImplemented

    @classmethod
    def encode(cls, payload: dict) -> str:
        return NotImplemented

    @classmethod
    def jws_encode(cls, payload: bytes, is_payload_detached: bool = True) -> str:
        return NotImplemented

    @classmethod
    def decode(
        cls, token: str, verify_expiration: bool = True, verify_aud: bool = False
    ) -> dict:
        return NotImplemented

    @classmethod
    def validate_configuration(cls):
        return NotImplemented

    @classmethod
    def get_jwks(cls) -> dict:
        return NotImplemented

    @classmethod
    def get_key_id(cls) -> str:
        return NotImplemented

    @classmethod
    def get_issuer(cls) -> str:
        return NotImplemented


class JWTManager(JWTManagerBase):
    KEY_FILE_FOR_DEBUG = ".jwt_key.pem"

    @classmethod
    def get_domain(cls) -> str:
        return get_domain()

    @classmethod
    @cache
    def get_private_key(cls) -> rsa.RSAPrivateKey:
        pem = settings.RSA_PRIVATE_KEY
        if not pem:
            if settings.DEBUG:
                return cls._load_debug_private_key()
            raise ImproperlyConfigured(
                "RSA_PRIVATE_KEY is required when DEBUG mode is disabled."
            )
        return cls._get_private_key(pem)

    @classmethod
    def _get_private_key(cls, pem: str | bytes) -> rsa.RSAPrivateKey:
        if isinstance(pem, str):
            pem = pem.encode("utf-8")

        password: str | bytes | None = settings.RSA_PRIVATE_PASSWORD
        if isinstance(password, str):
            password = password.encode("utf-8")
        return cast(
            rsa.RSAPrivateKey,
            serialization.load_pem_private_key(pem, password=password),
        )

    @classmethod
    def _load_debug_private_key(cls) -> rsa.RSAPrivateKey:
        key_path = join(settings.PROJECT_ROOT, cls.KEY_FILE_FOR_DEBUG)
        if exists(key_path):
            return cls._load_local_private_key(key_path)

        return cls._create_local_private_key(key_path)

    @classmethod
    def _load_local_private_key(cls, path) -> rsa.RSAPrivateKey:
        with open(path, "rb") as key_file:
            return cast(
                rsa.RSAPrivateKey,
                serialization.load_pem_private_key(key_file.read(), password=None),
            )

    @classmethod
    def _create_local_private_key(cls, path) -> rsa.RSAPrivateKey:
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
    @cache
    def get_public_key(cls) -> rsa.RSAPublicKey:
        global PUBLIC_KEY

        if PUBLIC_KEY is None:
            private_key = cls.get_private_key()
            PUBLIC_KEY = private_key.public_key()
        return PUBLIC_KEY

    @classmethod
    def get_jwks(cls) -> dict:
        jwk_dict = json.loads(RSAAlgorithm.to_jwk(cls.get_public_key()))
        jwk_dict.update({"use": "sig", "kid": cls.get_key_id()})
        return {"keys": [jwk_dict]}

    @classmethod
    def get_key_id(cls) -> str:
        """Generate JWT key ID for the public key.

        This generates a "thumbprint" as 'kid' field using RFC 7638 implementation
        based on the RSA public key.
        """
        public_key_pem = cls.get_public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        jwk = JsonWebKey.import_key(public_key_pem)
        return jwk.thumbprint()

    @classmethod
    def encode(cls, payload):
        return api_jwt.encode(
            payload,
            cls.get_private_key(),
            algorithm="RS256",
            headers={"kid": cls.get_key_id()},
        )

    @classmethod
    def jws_encode(cls, payload: bytes, is_payload_detached: bool = True) -> str:
        return api_jws.encode(
            payload,
            key=cls.get_private_key(),
            algorithm="RS256",
            headers={"kid": cls.get_key_id(), "crit": ["b64"]},
            is_payload_detached=is_payload_detached,
        )

    @classmethod
    def decode(cls, token, verify_expiration: bool = True, verify_aud: bool = False):
        # `verify_aud` set to false as we decode our own tokens
        # we can have `aud` defined for app or custom.
        headers = jwt.get_unverified_header(token)
        if headers.get("alg") == "RS256":
            return jwt.decode(
                token,
                cls.get_public_key(),
                algorithms=["RS256"],
                options={"verify_exp": verify_expiration, "verify_aud": verify_aud},
            )
        return jwt.decode(
            token,
            cast(str, settings.SECRET_KEY),
            algorithms=["HS256"],
            options={"verify_exp": verify_expiration, "verify_aud": verify_aud},
        )

    @classmethod
    def validate_configuration(cls):
        if not settings.RSA_PRIVATE_KEY:
            if not settings.DEBUG:
                raise ImproperlyConfigured(
                    "Variable RSA_PRIVATE_KEY is not provided. "
                    "It is required for running in not DEBUG mode."
                )
            msg = (
                "RSA_PRIVATE_KEY is missing. Using temporary key for local "
                "development with DEBUG mode."
            )
            logger.warning(color_style().WARNING(msg))

        cls.get_private_key.cache_clear()
        cls.get_public_key.cache_clear()
        try:
            cls.get_private_key()
        except Exception as e:
            raise ImproperlyConfigured(
                f"Unable to load provided PEM private key. {e}"
            ) from e

    @classmethod
    def get_issuer(cls) -> str:
        return build_absolute_uri(reverse("api"), domain=cls.get_domain())


@cache
def get_jwt_manager() -> JWTManagerBase:
    return import_string(settings.JWT_MANAGER_PATH)
