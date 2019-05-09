# coding: utf-8
from __future__ import unicode_literals

from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):

    def day_of_week(self):
        day = self.date('%w')
        DAY_NAMES = {
            "0": "일요일",
            "1": "월요일",
            "2": "화요일",
            "3": "수요일",
            "4": "목요일",
            "5": "금요일",
            "6": "토요일",
        }
        return DAY_NAMES[day]

    def month_name(self):
        month = self.month()
        MONTH_NAMES = {
            "01": "1월",
            "02": "2월",
            "03": "3월",
            "04": "4월",
            "05": "5월",
            "06": "6월",
            "07": "7월",
            "08": "8월",
            "09": "9월",
            "10": "10월",
            "11": "11월",
            "12": "12월",
        }
        return MONTH_NAMES[month]
