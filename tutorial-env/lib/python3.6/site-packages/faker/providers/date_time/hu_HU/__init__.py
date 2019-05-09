# coding: utf-8

from __future__ import unicode_literals
from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):

    def day_of_week(self):
        day = self.date('%w')
        DAY_NAMES = {
            "0": "hétfő",
            "1": "kedd",
            "2": "szerda",
            "3": "csütörtök",
            "4": "péntek",
            "5": "szombat",
            "6": "vasárnap",
        }

        return DAY_NAMES[day]

    def month_name(self):
        month = self.month()
        MONTH_NAMES = {
            "01": "január",
            "02": "február",
            "03": "március",
            "04": "április",
            "05": "május",
            "06": "junius",
            "07": "julius",
            "08": "augusztus",
            "09": "szeptember",
            "10": "október",
            "11": "november",
            "12": "december",
        }

        return MONTH_NAMES[month]
