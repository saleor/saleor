from datetime import datetime

import graphene
import jwt

from ..account.models import User
from ..settings import JWT_EXPIRATION_DELTA, JWT_REFRESH_EXPIRATION_DELTA, JWT_SECRET

JWT_ALGORITHM = "HS256"
JWT_AUTH_HEADER = "HTTP_AUTHORIZATION"
JWT_AUTH_HEADER_PREFIX = "JWT"
JWT_ACCESS_TYPE = "access"
JWT_REFRESH_TYPE = "refresh"
JWT_REFRESH_TOKEN_COOKIE_NAME = "refreshToken"


def jwt_base_payload(exp_delta):
    payload = {
        "exp": datetime.utcnow() + exp_delta,
        "iat": datetime.utcnow(),
    }
    return payload


def jwt_user_payload(user, token_type, exp_delta, additional_payload=None):
    payload = jwt_base_payload(exp_delta)
    payload.update(
        {
            "email": user.email,
            "type": token_type,
            "user_id": graphene.Node.to_global_id("User", user.id),
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        }
    )
    if additional_payload:
        payload.update(additional_payload)
    return payload


def jwt_encode(payload):
    return jwt.encode(payload, JWT_SECRET, JWT_ALGORITHM,).decode("utf-8")


def jwt_decode(token):
    return jwt.decode(token, JWT_SECRET, algorithms=JWT_ALGORITHM)


def create_token(payload, exp_delta):
    payload.update(jwt_base_payload(exp_delta))
    return jwt_encode(payload)


def create_access_token(user, additional_payload=None):
    payload = jwt_user_payload(
        user, JWT_ACCESS_TYPE, JWT_EXPIRATION_DELTA, additional_payload
    )
    return jwt_encode(payload)


def create_refresh_token(user, additional_payload=None):
    payload = jwt_user_payload(
        user, JWT_REFRESH_TYPE, JWT_REFRESH_EXPIRATION_DELTA, additional_payload
    )
    return jwt_encode(payload)


def get_token_from_request(request):
    auth = request.META.get(JWT_AUTH_HEADER, "").split()
    prefix = JWT_AUTH_HEADER_PREFIX

    if len(auth) != 2 or auth[0].lower() != prefix.lower():
        return None
    return auth[1]


def get_user_from_access_token(token):
    payload = jwt_decode(token)
    if payload["type"] != JWT_ACCESS_TYPE:
        return None
    return User.objects.filter(email=payload["email"], is_active=True).first()
