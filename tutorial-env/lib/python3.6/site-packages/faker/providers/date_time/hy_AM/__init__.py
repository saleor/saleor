# coding: utf-8

from __future__ import unicode_literals
from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):

    DAY_NAMES = {
        "0": "Կիրակի",
        "1": "Երկուշաբթի",
        "2": "Երեքշաբթի",
        "3": "Չորեքշաբթի",
        "4": "Հինգշաբթի",
        "5": "Ուրբաթ",
        "6": "Շաբաթ",
    }

    MONTH_NAMES = {
        "01": "Հունվար",
        "02": "Փետրվար",
        "03": "Մարտ",
        "04": "Ապրիլ",
        "05": "Մայիս",
        "06": "Հունիս",
        "07": "Հուլիս",
        "08": "Օգոստոս",
        "09": "Սեպտեմբեր",
        "10": "Հոկտեմբեր",
        "11": "Նոյեմբեր",
        "12": "Դեկտեմբեր",
    }

    def day_of_week(self):
        day = self.date('%w')
        return self.DAY_NAMES[day]

    def month_name(self):
        month = self.month()
        return self.MONTH_NAMES[month]
