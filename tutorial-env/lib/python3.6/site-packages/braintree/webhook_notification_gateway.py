import re
import sys
if sys.version_info[0] == 2:
    from base64 import decodestring as decodebytes
else:
    from base64 import decodebytes
import sys
from braintree.exceptions.invalid_signature_error import InvalidSignatureError
from braintree.exceptions.invalid_challenge_error import InvalidChallengeError
from braintree.util.crypto import Crypto
from braintree.util.xml_util import XmlUtil
from braintree.webhook_notification import WebhookNotification

if sys.version_info[0] == 2:
    text_type = unicode
else:
    text_type = str

class WebhookNotificationGateway(object):
    def __init__(self, gateway):
        self.gateway = gateway
        self.config = gateway.config

    def parse(self, signature, payload):
        if signature is None:
            raise InvalidSignatureError("signature cannot be blank")
        if payload is None:
            raise InvalidSignatureError("payload cannot be blank")
        if isinstance(payload, text_type):
            payload = payload.encode('ascii')
        if re.search(b"[^A-Za-z0-9+=/\n]", payload):
            raise InvalidSignatureError("payload contains illegal characters")
        self.__validate_signature(signature, payload)
        attributes = XmlUtil.dict_from_xml(decodebytes(payload))
        return WebhookNotification(self.gateway, attributes['notification'])

    def verify(self, challenge):
        if not re.match("^[a-f0-9]{20,32}$", challenge):
            raise InvalidChallengeError("challenge contains non-hex characters")
        digest = Crypto.sha1_hmac_hash(self.config.private_key, challenge)
        return "%s|%s" % (self.config.public_key, digest)

    def __matching_signature(self, signature_pairs):
        for public_key, signature in signature_pairs:
            if public_key == self.config.public_key:
                return signature
        return None

    def __validate_signature(self, signature_string, payload):
        signature_pairs = [pair.split("|") for pair in signature_string.split("&") if "|" in pair]
        signature = self.__matching_signature(signature_pairs)
        if not signature:
            raise InvalidSignatureError("no matching public key")
        if not any(self.__payload_matches(signature, p) for p in [payload, payload + b"\n"]):
            raise InvalidSignatureError("signature does not match payload - one has been modified")

    def __payload_matches(self, signature, payload):
        payload_signature = Crypto.sha1_hmac_hash(self.config.private_key, payload)
        return Crypto.secure_compare(payload_signature, signature)
