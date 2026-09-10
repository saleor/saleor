from ...core.jwt_manager import get_jwt_manager


def signature_for_payload(body: bytes):
    return get_jwt_manager().jws_encode(body)
