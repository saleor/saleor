# coding: utf-8
from __future__ import unicode_literals

from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):

    def day_of_week(self):
        day = self.date('%w')
        DAY_NAMES = {
            "0": "Nedjelja",
            "1": "Ponedjeljak",
            "2": "Utorak",
            "3": "Srijeda",
            "4": "Četvrtak",
            "5": "Petak",
            "6": "Subota",
        }
        return DAY_NAMES[day]

    def month_name(self):
        month = self.month()
        MONTH_NAMES = {
            "01": "Siječanj",
            "02": "Veljača",
            "03": "Ožujak",
            "04": "Travanj",
            "05": "Svibanj",
            "06": "Lipanj",
            "07": "Srpanj",
            "08": "Kolovoz",
            "09": "Rujan",
            "10": "Listopad",
            "11": "Studeni",
            "12": "Prosinac",
        }
        return MONTH_NAMES[month]
