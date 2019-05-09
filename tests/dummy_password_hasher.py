from collections import OrderedDict

from django.contrib.auth.hashers import BasePasswordHasher
from django.utils.translation import pgettext_lazy


class DummyHasher(BasePasswordHasher):
    """Dummy password hasher used only for unit tests purpose. Overwriting
    default Django password hasher significantly reduces the time of tests
    execution."""

    algorithm = "dummy"

    def encode(self, password, *args):
        assert password is not None
        return "%s$%s" % (self.algorithm, password)

    def verify(self, password, encoded):
        algorithm, dummy_password = encoded.split("$")
        assert algorithm == self.algorithm
        return password == dummy_password

    def safe_summary(self, encoded):
        algorithm, dummy_password = encoded.split("$")
        return OrderedDict(
            [
                (pgettext_lazy("algorithm"), algorithm),
                (pgettext_lazy("hash"), dummy_password),
            ]
        )

    def harden_runtime(self, password, encoded):
        pass
