import hashlib
import urllib
import urllib.parse


def generate_signature(merchant_passphrase: str, payload: dict) -> str:
    """
    Generate the signature salted with the passphrase.
    https://developers.payfast.co.za/api#authentication
    :param merchant_passphrase:
    :param payload:
    :return: signature
    """
    payload_response = ""
    payload["passphrase"] = merchant_passphrase
    sorted_payload_keys = sorted(payload)
    for key in sorted_payload_keys:
        # Get all the data for PayFast and prepare parameter string
        payload_response += key + "=" + urllib.parse.quote_plus(str(payload[key])) + "&"
    # After looping through remove the last &
    del payload["passphrase"]
    payload_response = payload_response[:-1]
    return hashlib.md5(payload_response.encode()).hexdigest()
