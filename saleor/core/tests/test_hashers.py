from ..hashers import SHA512Base64PBKDF2PasswordHasher


def test_encode_and_verify_sha512_base64_pbkdf2():
    generated_token = SHA512Base64PBKDF2PasswordHasher().encode(
        "Saleor123!", salt=SHA512Base64PBKDF2PasswordHasher().salt()
    )
    assert 90 == len(generated_token)
    assert SHA512Base64PBKDF2PasswordHasher().verify("Saleor123!", generated_token)
