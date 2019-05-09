# -*- coding: utf-8 -*-

from .base import BaseCompressor


class IdentityCompressor(BaseCompressor):
    def compress(self, value):
        return value

    def decompress(self, value):
        return value
