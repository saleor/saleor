# coding: utf-8

from __future__ import unicode_literals

from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):

    DAY_NAMES = {
        '0': 'poniedziałek',
        '1': 'wtorek',
        '2': 'środa',
        '3': 'czwartek',
        '4': 'piątek',
        '5': 'sobota',
        '6': 'niedziela',
    }

    MONTH_NAMES = {
        '01': 'styczeń',
        '02': 'luty',
        '03': 'marzec',
        '04': 'kwiecień',
        '05': 'maj',
        '06': 'czerwiec',
        '07': 'lipiec',
        '08': 'sierpień',
        '09': 'wrzesień',
        '10': 'październik',
        '11': 'listopad',
        '12': 'grudzień',
    }

    def day_of_week(self):
        day = self.date('%w')
        return self.DAY_NAMES[day]

    def month_name(self):
        month = self.month()
        return self.MONTH_NAMES[month]
