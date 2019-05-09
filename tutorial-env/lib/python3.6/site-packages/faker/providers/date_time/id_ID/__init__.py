# coding: utf-8

from __future__ import unicode_literals
from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):

    def day_of_week(self):
        day = self.date('%w')
        DAY_NAMES = {
            "0": "Senin",
            "1": "Selasa",
            "2": "Rabu",
            "3": "Kamis",
            "4": "Jumat",
            "5": "Sabtu",
            "6": "Minggu",
        }

        return DAY_NAMES[day]

    def month_name(self):
        month = self.month()
        MONTH_NAMES = {
            "01": "Januari",
            "02": "Februari",
            "03": "Maret",
            "04": "April",
            "05": "Mei",
            "06": "Juni",
            "07": "Juli",
            "08": "Agustus",
            "09": "September",
            "10": "Oktober",
            "11": "November",
            "12": "Desember",
        }

        return MONTH_NAMES[month]
