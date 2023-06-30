import pytest
from ..hashers import SHA512Base64PBKDF2PasswordHasher


def test_migration_from_sha512_base64_to_sha512_base64_pbkdf2():
    original_token = "GYZwGbUT4VFqNgejNlAabTyI0UAyK1nWm7Bs5ME5K9lIn47s4D43SucLFGor3DRnolbnI9QD7zZerO7hhLyCpQ=="
    migrated_token = SHA512Base64PBKDF2PasswordHasher().PBKDF2_round(
        password=original_token,
        salt=SHA512Base64PBKDF2PasswordHasher().salt()
    )
    
    assert SHA512Base64PBKDF2PasswordHasher().verify(
        "Breitling123!",
        migrated_token
    )

def test_encode_and_verify_sha512_base64_pbkdf2():
    generated_token = SHA512Base64PBKDF2PasswordHasher().encode(
        "Breitling123!", salt=SHA512Base64PBKDF2PasswordHasher().salt()
    )
    
    assert 90 == len(generated_token)
    assert SHA512Base64PBKDF2PasswordHasher().verify(
        "Breitling123!",
        generated_token
    )
    
