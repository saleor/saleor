# coding=utf-8

from __future__ import unicode_literals

import re

from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    # Source:
    # https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Saudi_Arabia
    LICENSE_FORMAT_EN = '#### ???'
    LICENSE_FORMAT_AR = '? ? ? ####'

    PLATE_CHARS_EN = 'ABDEGHJKLNRSTUVXZ'
    PLATE_CHARS_AR = 'أبدعقهحكلنرسطوىصم'

    PLATE_MAP = {
        'A': 'ا',
        'B': 'ب',
        'D': 'د',
        'E': 'ع',
        'G': 'ق',
        'H': 'ه',
        'J': 'ح',
        'K': 'ك',
        'L': 'ل',
        'N': 'ن',
        'R': 'ر',
        'S': 'س',
        'T': 'ط',
        'U': 'و',
        'V': 'ى',
        'X': 'ص',
        'Z': 'م',

        '0': '٠',
        '1': '١',
        '2': '٢',
        '3': '٣',
        '4': '٤',
        '5': '٥',
        '6': '٦',
        '7': '٧',
        '8': '٨',
        '9': '٩',
    }

    def license_plate_en(self):
        return self.bothify(
            self.LICENSE_FORMAT_EN, letters=self.PLATE_CHARS_EN,
        )

    def license_plate_ar(self):
        english_plate = self.license_plate_en()
        return self._translate_license_plate(english_plate)

    def _translate_license_plate(self, license_plate):
        nums = list(reversed(license_plate[0:4]))
        chars = list(license_plate[5:8])

        numerated = re.sub(
            r'\#',
            lambda x: self.PLATE_MAP[nums.pop()],
            self.LICENSE_FORMAT_AR,
        )
        ar_plate = re.sub(
            r'\?',
            lambda x: self.PLATE_MAP[chars.pop()],
            numerated,
        )

        return ar_plate

    def license_plate(self):
        en_palate = self.license_plate_en()
        ar_palate = self._translate_license_plate(en_palate)

        return en_palate, ar_palate
