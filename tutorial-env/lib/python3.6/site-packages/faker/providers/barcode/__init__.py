# coding=utf-8

from __future__ import unicode_literals
from .. import BaseProvider


class Provider(BaseProvider):

    def ean(self, length=13):
        code = [self.random_digit() for _ in range(length - 1)]

        if length not in (8, 13):
            raise AssertionError("length can only be 8 or 13")

        if length == 8:
            weights = [3, 1, 3, 1, 3, 1, 3]
        elif length == 13:
            weights = [1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3]

        weighted_sum = sum(x * y for x, y in zip(code, weights))
        check_digit = (10 - weighted_sum % 10) % 10
        code.append(check_digit)

        return ''.join(str(x) for x in code)

    def ean8(self):
        return self.ean(8)

    def ean13(self):
        return self.ean(13)
