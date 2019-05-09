# -*- coding: utf-8 -*-


class BaseCompressor(object):
    def __init__(self, options):
        self._options = options

    def compress(self, value):
        raise NotImplementedError

    def decompress(self, value):
        raise NotImplementedError
