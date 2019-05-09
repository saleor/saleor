# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as SsnProvider


class Provider(SsnProvider):

    def ssn(self):
        """
        Returns an Israeli identity number, known as Teudat Zehut ("tz").

        https://en.wikipedia.org/wiki/Israeli_identity_card
        """

        newID = str(self.generator.random.randrange(111111, 99999999))
        newID = newID.zfill(8)
        theSum = 0
        indexRange = [0, 2, 4, 6]
        for i in indexRange:
            digit = newID[i]
            num = int(digit)
            theSum = theSum + num
            num = int(newID[i + 1]) * 2
            if num > 9:
                num = int(str(num)[0]) + int(str(num)[1])
            theSum = theSum + num
        lastDigit = theSum % 10
        if lastDigit != 0:
            lastDigit = 10 - lastDigit

        return str(newID) + str(lastDigit)
