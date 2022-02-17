from random import randint

from django.conf import settings
from django.db import models


def generate_otp():
    return "".join([str(randint(0, 9)) for _ in range(6)])


class OTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=6, default=generate_otp)
    issued_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.code
