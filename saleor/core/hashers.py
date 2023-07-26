import base64
import hashlib

from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.utils.encoding import force_bytes


class SHA512Base64PBKDF2PasswordHasher(PBKDF2PasswordHasher):
    """Hasher for Symfony migrated password tokens.

    5000 iterations of sha512 plus base64 encoder, with an extra
    PBKDF2 round.
    """

    algorithm = "sha512b64pbkdf2"
    iterations = 690000

    def encode(self, password, salt, iterations=None):
        symfony_iterations = 5000
        digest = hashlib.sha512(force_bytes(password, encoding="ISO-8859-1")).digest()
        for i in range(symfony_iterations - 1):
            digest = hashlib.sha512(
                digest + force_bytes(password, encoding="ISO-8859-1")
            ).digest()
        iterations = iterations or self.iterations
        return self.pbkdf2_round(
            base64.b64encode(digest).decode("ISO-8859-1"), salt, iterations
        )

    def pbkdf2_round(self, password, salt, iterations=None):
        """PBKDF2 round (salt + secure hash function added)."""
        return super().encode(password, salt, iterations)
