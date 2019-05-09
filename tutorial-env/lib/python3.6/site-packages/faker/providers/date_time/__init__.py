# coding=utf-8

from __future__ import unicode_literals

import re

from calendar import timegm
from datetime import timedelta, MAXYEAR
from time import time

from dateutil import relativedelta
from dateutil.tz import tzlocal, tzutc

from faker.utils import is_string
from faker.utils.datetime_safe import date, datetime, real_date, real_datetime

from .. import BaseProvider

localized = True


def datetime_to_timestamp(dt):
    if getattr(dt, 'tzinfo', None) is not None:
        dt = dt.astimezone(tzutc())
    return timegm(dt.timetuple())


def timestamp_to_datetime(timestamp, tzinfo):
    if tzinfo is None:
        pick = datetime.fromtimestamp(timestamp, tzlocal())
        pick = pick.astimezone(tzutc()).replace(tzinfo=None)
    else:
        pick = datetime.fromtimestamp(timestamp, tzinfo)

    return pick


class ParseError(ValueError):
    pass


timedelta_pattern = r''
for name, sym in [('years', 'y'), ('months', 'M'), ('weeks', 'w'), ('days', 'd'),
                  ('hours', 'h'), ('minutes', 'm'), ('seconds', 's')]:
    timedelta_pattern += r'((?P<{0}>(?:\+|-)\d+?){1})?'.format(name, sym)


class Provider(BaseProvider):
    centuries = [
        'I',
        'II',
        'III',
        'IV',
        'V',
        'VI',
        'VII',
        'VIII',
        'IX',
        'X',
        'XI',
        'XII',
        'XIII',
        'XIV',
        'XV',
        'XVI',
        'XVII',
        'XVIII',
        'XIX',
        'XX',
        'XXI']

    countries = [{'timezones': ['Europe/Andorra'],
                  'alpha-2-code': 'AD',
                  'alpha-3-code': 'AND',
                  'continent': 'Europe',
                  'name': 'Andorra',
                  'capital': 'Andorra la Vella'},
                 {'timezones': ['Asia/Kabul'],
                  'alpha-2-code': 'AF',
                  'alpha-3-code': 'AFG',
                  'continent': 'Asia',
                  'name': 'Afghanistan',
                  'capital': 'Kabul'},
                 {'timezones': ['America/Antigua'],
                  'alpha-2-code': 'AG',
                  'alpha-3-code': 'ATG',
                  'continent': 'North America',
                  'name': 'Antigua and Barbuda',
                  'capital': "St. John's"},
                 {'timezones': ['Europe/Tirane'],
                  'alpha-2-code': 'AL',
                  'alpha-3-code': 'ALB',
                  'continent': 'Europe',
                  'name': 'Albania',
                  'capital': 'Tirana'},
                 {'timezones': ['Asia/Yerevan'],
                  'alpha-2-code': 'AM',
                  'alpha-3-code': 'ARM',
                  'continent': 'Asia',
                  'name': 'Armenia',
                  'capital': 'Yerevan'},
                 {'timezones': ['Africa/Luanda'],
                  'alpha-2-code': 'AO',
                  'alpha-3-code': 'AGO',
                  'continent': 'Africa',
                  'name': 'Angola',
                  'capital': 'Luanda'},
                 {'timezones': ['America/Argentina/Buenos_Aires',
                                'America/Argentina/Cordoba',
                                'America/Argentina/Jujuy',
                                'America/Argentina/Tucuman',
                                'America/Argentina/Catamarca',
                                'America/Argentina/La_Rioja',
                                'America/Argentina/San_Juan',
                                'America/Argentina/Mendoza',
                                'America/Argentina/Rio_Gallegos',
                                'America/Argentina/Ushuaia'],
                  'alpha-2-code': 'AR',
                  'alpha-3-code': 'ARG',
                  'continent': 'South America',
                  'name': 'Argentina',
                  'capital': 'Buenos Aires'},
                 {'timezones': ['Europe/Vienna'],
                  'alpha-2-code': 'AT',
                  'alpha-3-code': 'AUT',
                  'continent': 'Europe',
                  'name': 'Austria',
                  'capital': 'Vienna'},
                 {'timezones': ['Australia/Lord_Howe',
                                'Australia/Hobart',
                                'Australia/Currie',
                                'Australia/Melbourne',
                                'Australia/Sydney',
                                'Australia/Broken_Hill',
                                'Australia/Brisbane',
                                'Australia/Lindeman',
                                'Australia/Adelaide',
                                'Australia/Darwin',
                                'Australia/Perth'],
                  'alpha-2-code': 'AU',
                  'alpha-3-code': 'AUS',
                  'continent': 'Oceania',
                  'name': 'Australia',
                  'capital': 'Canberra'},
                 {'timezones': ['Asia/Baku'],
                  'alpha-2-code': 'AZ',
                  'alpha-3-code': 'AZE',
                  'continent': 'Asia',
                  'name': 'Azerbaijan',
                  'capital': 'Baku'},
                 {'timezones': ['America/Barbados'],
                  'alpha-2-code': 'BB',
                  'alpha-3-code': 'BRB',
                  'continent': 'North America',
                  'name': 'Barbados',
                  'capital': 'Bridgetown'},
                 {'timezones': ['Asia/Dhaka'],
                  'alpha-2-code': 'BD',
                  'alpha-3-code': 'BGD',
                  'continent': 'Asia',
                  'name': 'Bangladesh',
                  'capital': 'Dhaka'},
                 {'timezones': ['Europe/Brussels'],
                  'alpha-2-code': 'BE',
                  'alpha-3-code': 'BEL',
                  'continent': 'Europe',
                  'name': 'Belgium',
                  'capital': 'Brussels'},
                 {'timezones': ['Africa/Ouagadougou'],
                  'alpha-2-code': 'BF',
                  'alpha-3-code': 'BFA',
                  'continent': 'Africa',
                  'name': 'Burkina Faso',
                  'capital': 'Ouagadougou'},
                 {'timezones': ['Europe/Sofia'],
                  'alpha-2-code': 'BG',
                  'alpha-3-code': 'BGR',
                  'continent': 'Europe',
                  'name': 'Bulgaria',
                  'capital': 'Sofia'},
                 {'timezones': ['Asia/Bahrain'],
                  'alpha-2-code': 'BH',
                  'alpha-3-code': 'BHR',
                  'continent': 'Asia',
                  'name': 'Bahrain',
                  'capital': 'Manama'},
                 {'timezones': ['Africa/Bujumbura'],
                  'alpha-2-code': 'BI',
                  'alpha-3-code': 'BDI',
                  'continent': 'Africa',
                  'name': 'Burundi',
                  'capital': 'Bujumbura'},
                 {'timezones': ['Africa/Porto-Novo'],
                  'alpha-2-code': 'BJ',
                  'alpha-3-code': 'BEN',
                  'continent': 'Africa',
                  'name': 'Benin',
                  'capital': 'Porto-Novo'},
                 {'timezones': ['Asia/Brunei'],
                  'alpha-2-code': 'BN',
                  'alpha-3-code': 'BRN',
                  'continent': 'Asia',
                  'name': 'Brunei Darussalam',
                  'capital': 'Bandar Seri Begawan'},
                 {'timezones': ['America/La_Paz'],
                  'alpha-2-code': 'BO',
                  'alpha-3-code': 'BOL',
                  'continent': 'South America',
                  'name': 'Bolivia',
                  'capital': 'Sucre'},
                 {'timezones': ['America/Noronha',
                                'America/Belem',
                                'America/Fortaleza',
                                'America/Recife',
                                'America/Araguaina',
                                'America/Maceio',
                                'America/Bahia',
                                'America/Sao_Paulo',
                                'America/Campo_Grande',
                                'America/Cuiaba',
                                'America/Porto_Velho',
                                'America/Boa_Vista',
                                'America/Manaus',
                                'America/Eirunepe',
                                'America/Rio_Branco'],
                  'alpha-2-code': 'BR',
                  'alpha-3-code': 'BRA',
                  'continent': 'South America',
                  'name': 'Brazil',
                  'capital': 'Bras\xc3\xadlia'},
                 {'timezones': ['America/Nassau'],
                  'alpha-2-code': 'BS',
                  'alpha-3-code': 'BHS',
                  'continent': 'North America',
                  'name': 'Bahamas',
                  'capital': 'Nassau'},
                 {'timezones': ['Asia/Thimphu'],
                  'alpha-2-code': 'BT',
                  'alpha-3-code': 'BTN',
                  'continent': 'Asia',
                  'name': 'Bhutan',
                  'capital': 'Thimphu'},
                 {'timezones': ['Africa/Gaborone'],
                  'alpha-2-code': 'BW',
                  'alpha-3-code': 'BWA',
                  'continent': 'Africa',
                  'name': 'Botswana',
                  'capital': 'Gaborone'},
                 {'timezones': ['Europe/Minsk'],
                  'alpha-2-code': 'BY',
                  'alpha-3-code': 'BLR',
                  'continent': 'Europe',
                  'name': 'Belarus',
                  'capital': 'Minsk'},
                 {'timezones': ['America/Belize'],
                  'alpha-2-code': 'BZ',
                  'alpha-3-code': 'BLZ',
                  'continent': 'North America',
                  'name': 'Belize',
                  'capital': 'Belmopan'},
                 {'timezones': ['America/St_Johns',
                                'America/Halifax',
                                'America/Glace_Bay',
                                'America/Moncton',
                                'America/Goose_Bay',
                                'America/Blanc-Sablon',
                                'America/Montreal',
                                'America/Toronto',
                                'America/Nipigon',
                                'America/Thunder_Bay',
                                'America/Pangnirtung',
                                'America/Iqaluit',
                                'America/Atikokan',
                                'America/Rankin_Inlet',
                                'America/Winnipeg',
                                'America/Rainy_River',
                                'America/Cambridge_Bay',
                                'America/Regina',
                                'America/Swift_Current',
                                'America/Edmonton',
                                'America/Yellowknife',
                                'America/Inuvik',
                                'America/Dawson_Creek',
                                'America/Vancouver',
                                'America/Whitehorse',
                                'America/Dawson'],
                  'alpha-2-code': 'CA',
                  'alpha-3-code': 'CAN',
                  'continent': 'North America',
                  'name': 'Canada',
                  'capital': 'Ottawa'},
                 {'timezones': ['Africa/Kinshasa',
                                'Africa/Lubumbashi'],
                  'alpha-2-code': 'CD',
                  'alpha-3-code': 'COD',
                  'continent': 'Africa',
                  'name': 'Democratic Republic of the Congo',
                  'capital': 'Kinshasa'},
                 {'timezones': ['Africa/Brazzaville'],
                  'alpha-2-code': 'CG',
                  'alpha-3-code': 'COG',
                  'continent': 'Africa',
                  'name': 'Republic of the Congo',
                  'capital': 'Brazzaville'},
                 {'timezones': ['Africa/Abidjan'],
                  'alpha-2-code': 'CI',
                  'alpha-3-code': 'CIV',
                  'continent': 'Africa',
                  'name': "C\xc3\xb4te d'Ivoire",
                  'capital': 'Yamoussoukro'},
                 {'timezones': ['America/Santiago',
                                'Pacific/Easter'],
                  'alpha-2-code': 'CL',
                  'alpha-3-code': 'CHL',
                  'continent': 'South America',
                  'name': 'Chile',
                  'capital': 'Santiago'},
                 {'timezones': ['Africa/Douala'],
                  'alpha-2-code': 'CM',
                  'alpha-3-code': 'CMR',
                  'continent': 'Africa',
                  'name': 'Cameroon',
                  'capital': 'Yaound\xc3\xa9'},
                 {'timezones': ['Asia/Shanghai',
                                'Asia/Harbin',
                                'Asia/Chongqing',
                                'Asia/Urumqi',
                                'Asia/Kashgar'],
                  'alpha-2-code': 'CN',
                  'alpha-3-code': 'CHN',
                  'continent': 'Asia',
                  'name': "People's Republic of China",
                  'capital': 'Beijing'},
                 {'timezones': ['America/Bogota'],
                  'alpha-2-code': 'CO',
                  'alpha-3-code': 'COL',
                  'continent': 'South America',
                  'name': 'Colombia',
                  'capital': 'Bogot\xc3\xa1'},
                 {'timezones': ['America/Costa_Rica'],
                  'alpha-2-code': 'CR',
                  'alpha-3-code': 'CRI',
                  'continent': 'North America',
                  'name': 'Costa Rica',
                  'capital': 'San Jos\xc3\xa9'},
                 {'timezones': ['America/Havana'],
                  'alpha-2-code': 'CU',
                  'alpha-3-code': 'CUB',
                  'continent': 'North America',
                  'name': 'Cuba',
                  'capital': 'Havana'},
                 {'timezones': ['Atlantic/Cape_Verde'],
                  'alpha-2-code': 'CV',
                  'alpha-3-code': 'CPV',
                  'continent': 'Africa',
                  'name': 'Cape Verde',
                  'capital': 'Praia'},
                 {'timezones': ['Asia/Nicosia'],
                  'alpha-2-code': 'CY',
                  'alpha-3-code': 'CYP',
                  'continent': 'Asia',
                  'name': 'Cyprus',
                  'capital': 'Nicosia'},
                 {'timezones': ['Europe/Prague'],
                  'alpha-2-code': 'CZ',
                  'alpha-3-code': 'CZE',
                  'continent': 'Europe',
                  'name': 'Czech Republic',
                  'capital': 'Prague'},
                 {'timezones': ['Europe/Berlin'],
                  'alpha-2-code': 'DE',
                  'alpha-3-code': 'DEU',
                  'continent': 'Europe',
                  'name': 'Germany',
                  'capital': 'Berlin'},
                 {'timezones': ['Africa/Djibouti'],
                  'alpha-2-code': 'DJ',
                  'alpha-3-code': 'DJI',
                  'continent': 'Africa',
                  'name': 'Djibouti',
                  'capital': 'Djibouti City'},
                 {'timezones': ['Europe/Copenhagen'],
                  'alpha-2-code': 'DK',
                  'alpha-3-code': 'DNK',
                  'continent': 'Europe',
                  'name': 'Denmark',
                  'capital': 'Copenhagen'},
                 {'timezones': ['America/Dominica'],
                  'alpha-2-code': 'DM',
                  'alpha-3-code': 'DMA',
                  'continent': 'North America',
                  'name': 'Dominica',
                  'capital': 'Roseau'},
                 {'timezones': ['America/Santo_Domingo'],
                  'alpha-2-code': 'DO',
                  'alpha-3-code': 'DOM',
                  'continent': 'North America',
                  'name': 'Dominican Republic',
                  'capital': 'Santo Domingo'},
                 {'timezones': ['America/Guayaquil',
                                'Pacific/Galapagos'],
                  'alpha-2-code': 'EC',
                  'alpha-3-code': 'ECU',
                  'continent': 'South America',
                  'name': 'Ecuador',
                  'capital': 'Quito'},
                 {'timezones': ['Europe/Tallinn'],
                  'alpha-2-code': 'EE',
                  'alpha-3-code': 'EST',
                  'continent': 'Europe',
                  'name': 'Estonia',
                  'capital': 'Tallinn'},
                 {'timezones': ['Africa/Cairo'],
                  'alpha-2-code': 'EG',
                  'alpha-3-code': 'EGY',
                  'continent': 'Africa',
                  'name': 'Egypt',
                  'capital': 'Cairo'},
                 {'timezones': ['Africa/Asmera'],
                  'alpha-2-code': 'ER',
                  'alpha-3-code': 'ERI',
                  'continent': 'Africa',
                  'name': 'Eritrea',
                  'capital': 'Asmara'},
                 {'timezones': ['Africa/Addis_Ababa'],
                  'alpha-2-code': 'ET',
                  'alpha-3-code': 'ETH',
                  'continent': 'Africa',
                  'name': 'Ethiopia',
                  'capital': 'Addis Ababa'},
                 {'timezones': ['Europe/Helsinki'],
                  'alpha-2-code': 'FI',
                  'alpha-3-code': 'FIN',
                  'continent': 'Europe',
                  'name': 'Finland',
                  'capital': 'Helsinki'},
                 {'timezones': ['Pacific/Fiji'],
                  'alpha-2-code': 'FJ',
                  'alpha-3-code': 'FJI',
                  'continent': 'Oceania',
                  'name': 'Fiji',
                  'capital': 'Suva'},
                 {'timezones': ['Europe/Paris'],
                  'alpha-2-code': 'FR',
                  'alpha-3-code': 'FRA',
                  'continent': 'Europe',
                  'name': 'France',
                  'capital': 'Paris'},
                 {'timezones': ['Africa/Libreville'],
                  'alpha-2-code': 'GA',
                  'alpha-3-code': 'GAB',
                  'continent': 'Africa',
                  'name': 'Gabon',
                  'capital': 'Libreville'},
                 {'timezones': ['Asia/Tbilisi'],
                  'alpha-2-code': 'GE',
                  'alpha-3-code': 'GEO',
                  'continent': 'Asia',
                  'name': 'Georgia',
                  'capital': 'Tbilisi'},
                 {'timezones': ['Africa/Accra'],
                  'alpha-2-code': 'GH',
                  'alpha-3-code': 'GHA',
                  'continent': 'Africa',
                  'name': 'Ghana',
                  'capital': 'Accra'},
                 {'timezones': ['Africa/Banjul'],
                  'alpha-2-code': 'GM',
                  'alpha-3-code': 'GMB',
                  'continent': 'Africa',
                  'name': 'The Gambia',
                  'capital': 'Banjul'},
                 {'timezones': ['Africa/Conakry'],
                  'alpha-2-code': 'GN',
                  'alpha-3-code': 'GIN',
                  'continent': 'Africa',
                  'name': 'Guinea',
                  'capital': 'Conakry'},
                 {'timezones': ['Europe/Athens'],
                  'alpha-2-code': 'GR',
                  'alpha-3-code': 'GRC',
                  'continent': 'Europe',
                  'name': 'Greece',
                  'capital': 'Athens'},
                 {'timezones': ['America/Guatemala'],
                  'alpha-2-code': 'GT',
                  'alpha-3-code': 'GTM',
                  'continent': 'North America',
                  'name': 'Guatemala',
                  'capital': 'Guatemala City'},
                 {'timezones': ['America/Guatemala'],
                  'alpha-2-code': 'HT',
                  'alpha-3-code': 'HTI',
                  'continent': 'North America',
                  'name': 'Haiti',
                  'capital': 'Port-au-Prince'},
                 {'timezones': ['Africa/Bissau'],
                  'alpha-2-code': 'GW',
                  'alpha-3-code': 'GNB',
                  'continent': 'Africa',
                  'name': 'Guinea-Bissau',
                  'capital': 'Bissau'},
                 {'timezones': ['America/Guyana'],
                  'alpha-2-code': 'GY',
                  'alpha-3-code': 'GUY',
                  'continent': 'South America',
                  'name': 'Guyana',
                  'capital': 'Georgetown'},
                 {'timezones': ['America/Tegucigalpa'],
                  'alpha-2-code': 'HN',
                  'alpha-3-code': 'HND',
                  'continent': 'North America',
                  'name': 'Honduras',
                  'capital': 'Tegucigalpa'},
                 {'timezones': ['Europe/Budapest'],
                  'alpha-2-code': 'HU',
                  'alpha-3-code': 'HUN',
                  'continent': 'Europe',
                  'name': 'Hungary',
                  'capital': 'Budapest'},
                 {'timezones': ['Asia/Jakarta',
                                'Asia/Pontianak',
                                'Asia/Makassar',
                                'Asia/Jayapura'],
                  'alpha-2-code': 'ID',
                  'alpha-3-code': 'IDN',
                  'continent': 'Asia',
                  'name': 'Indonesia',
                  'capital': 'Jakarta'},
                 {'timezones': ['Europe/Dublin'],
                  'alpha-2-code': 'IE',
                  'alpha-3-code': 'IRL',
                  'continent': 'Europe',
                  'name': 'Republic of Ireland',
                  'capital': 'Dublin'},
                 {'timezones': ['Asia/Jerusalem'],
                  'alpha-2-code': 'IL',
                  'alpha-3-code': 'ISR',
                  'continent': 'Asia',
                  'name': 'Israel',
                  'capital': 'Jerusalem'},
                 {'timezones': ['Asia/Calcutta'],
                  'alpha-2-code': 'IN',
                  'alpha-3-code': 'IND',
                  'continent': 'Asia',
                  'name': 'India',
                  'capital': 'New Delhi'},
                 {'timezones': ['Asia/Baghdad'],
                  'alpha-2-code': 'IQ',
                  'alpha-3-code': 'IRQ',
                  'continent': 'Asia',
                  'name': 'Iraq',
                  'capital': 'Baghdad'},
                 {'timezones': ['Asia/Tehran'],
                  'alpha-2-code': 'IR',
                  'alpha-3-code': 'IRN',
                  'continent': 'Asia',
                  'name': 'Iran',
                  'capital': 'Tehran'},
                 {'timezones': ['Atlantic/Reykjavik'],
                  'alpha-2-code': 'IS',
                  'alpha-3-code': 'ISL',
                  'continent': 'Europe',
                  'name': 'Iceland',
                  'capital': 'Reykjav\xc3\xadk'},
                 {'timezones': ['Europe/Rome'],
                  'alpha-2-code': 'IT',
                  'alpha-3-code': 'ITA',
                  'continent': 'Europe',
                  'name': 'Italy',
                  'capital': 'Rome'},
                 {'timezones': ['America/Jamaica'],
                  'alpha-2-code': 'JM',
                  'alpha-3-code': 'JAM',
                  'continent': 'North America',
                  'name': 'Jamaica',
                  'capital': 'Kingston'},
                 {'timezones': ['Asia/Amman'],
                  'alpha-2-code': 'JO',
                  'alpha-3-code': 'JOR',
                  'continent': 'Asia',
                  'name': 'Jordan',
                  'capital': 'Amman'},
                 {'timezones': ['Asia/Tokyo'],
                  'alpha-2-code': 'JP',
                  'alpha-3-code': 'JPN',
                  'continent': 'Asia',
                  'name': 'Japan',
                  'capital': 'Tokyo'},
                 {'timezones': ['Africa/Nairobi'],
                  'alpha-2-code': 'KE',
                  'alpha-3-code': 'KEN',
                  'continent': 'Africa',
                  'name': 'Kenya',
                  'capital': 'Nairobi'},
                 {'timezones': ['Asia/Bishkek'],
                  'alpha-2-code': 'KG',
                  'alpha-3-code': 'KGZ',
                  'continent': 'Asia',
                  'name': 'Kyrgyzstan',
                  'capital': 'Bishkek'},
                 {'timezones': ['Pacific/Tarawa',
                                'Pacific/Enderbury',
                                'Pacific/Kiritimati'],
                  'alpha-2-code': 'KI',
                  'alpha-3-code': 'KIR',
                  'continent': 'Oceania',
                  'name': 'Kiribati',
                  'capital': 'Tarawa'},
                 {'timezones': ['Asia/Pyongyang'],
                  'alpha-2-code': 'KP',
                  'alpha-3-code': 'PRK',
                  'continent': 'Asia',
                  'name': 'North Korea',
                  'capital': 'Pyongyang'},
                 {'timezones': ['Asia/Seoul'],
                  'alpha-2-code': 'KR',
                  'alpha-3-code': 'KOR',
                  'continent': 'Asia',
                  'name': 'South Korea',
                  'capital': 'Seoul'},
                 {'timezones': ['Asia/Kuwait'],
                  'alpha-2-code': 'KW',
                  'alpha-3-code': 'KWT',
                  'continent': 'Asia',
                  'name': 'Kuwait',
                  'capital': 'Kuwait City'},
                 {'timezones': ['Asia/Beirut'],
                  'alpha-2-code': 'LB',
                  'alpha-3-code': 'LBN',
                  'continent': 'Asia',
                  'name': 'Lebanon',
                  'capital': 'Beirut'},
                 {'timezones': ['Europe/Vaduz'],
                  'alpha-2-code': 'LI',
                  'alpha-3-code': 'LIE',
                  'continent': 'Europe',
                  'name': 'Liechtenstein',
                  'capital': 'Vaduz'},
                 {'timezones': ['Africa/Monrovia'],
                  'alpha-2-code': 'LR',
                  'alpha-3-code': 'LBR',
                  'continent': 'Africa',
                  'name': 'Liberia',
                  'capital': 'Monrovia'},
                 {'timezones': ['Africa/Maseru'],
                  'alpha-2-code': 'LS',
                  'alpha-3-code': 'LSO',
                  'continent': 'Africa',
                  'name': 'Lesotho',
                  'capital': 'Maseru'},
                 {'timezones': ['Europe/Vilnius'],
                  'alpha-2-code': 'LT',
                  'alpha-3-code': 'LTU',
                  'continent': 'Europe',
                  'name': 'Lithuania',
                  'capital': 'Vilnius'},
                 {'timezones': ['Europe/Luxembourg'],
                  'alpha-2-code': 'LU',
                  'alpha-3-code': 'LUX',
                  'continent': 'Europe',
                  'name': 'Luxembourg',
                  'capital': 'Luxembourg City'},
                 {'timezones': ['Europe/Riga'],
                  'alpha-2-code': 'LV',
                  'alpha-3-code': 'LVA',
                  'continent': 'Europe',
                  'name': 'Latvia',
                  'capital': 'Riga'},
                 {'timezones': ['Africa/Tripoli'],
                  'alpha-2-code': 'LY',
                  'alpha-3-code': 'LBY',
                  'continent': 'Africa',
                  'name': 'Libya',
                  'capital': 'Tripoli'},
                 {'timezones': ['Indian/Antananarivo'],
                  'alpha-2-code': 'MG',
                  'alpha-3-code': 'MDG',
                  'continent': 'Africa',
                  'name': 'Madagascar',
                  'capital': 'Antananarivo'},
                 {'timezones': ['Pacific/Majuro',
                                'Pacific/Kwajalein'],
                  'alpha-2-code': 'MH',
                  'alpha-3-code': 'MHL',
                  'continent': 'Oceania',
                  'name': 'Marshall Islands',
                  'capital': 'Majuro'},
                 {'timezones': ['Europe/Skopje'],
                  'alpha-2-code': 'MK',
                  'alpha-3-code': 'MKD',
                  'continent': 'Europe',
                  'name': 'Macedonia',
                  'capital': 'Skopje'},
                 {'timezones': ['Africa/Bamako'],
                  'alpha-2-code': 'ML',
                  'alpha-3-code': 'MLI',
                  'continent': 'Africa',
                  'name': 'Mali',
                  'capital': 'Bamako'},
                 {'timezones': ['Asia/Rangoon'],
                  'alpha-2-code': 'MM',
                  'alpha-3-code': 'MMR',
                  'continent': 'Asia',
                  'name': 'Myanmar',
                  'capital': 'Naypyidaw'},
                 {'timezones': ['Asia/Ulaanbaatar',
                                'Asia/Hovd',
                                'Asia/Choibalsan'],
                  'alpha-2-code': 'MN',
                  'alpha-3-code': 'MNG',
                  'continent': 'Asia',
                  'name': 'Mongolia',
                  'capital': 'Ulaanbaatar'},
                 {'timezones': ['Africa/Nouakchott'],
                  'alpha-2-code': 'MR',
                  'alpha-3-code': 'MRT',
                  'continent': 'Africa',
                  'name': 'Mauritania',
                  'capital': 'Nouakchott'},
                 {'timezones': ['Europe/Malta'],
                  'alpha-2-code': 'MT',
                  'alpha-3-code': 'MLT',
                  'continent': 'Europe',
                  'name': 'Malta',
                  'capital': 'Valletta'},
                 {'timezones': ['Indian/Mauritius'],
                  'alpha-2-code': 'MU',
                  'alpha-3-code': 'MUS',
                  'continent': 'Africa',
                  'name': 'Mauritius',
                  'capital': 'Port Louis'},
                 {'timezones': ['Indian/Maldives'],
                  'alpha-2-code': 'MV',
                  'alpha-3-code': 'MDV',
                  'continent': 'Asia',
                  'name': 'Maldives',
                  'capital': 'Mal\xc3\xa9'},
                 {'timezones': ['Africa/Blantyre'],
                  'alpha-2-code': 'MW',
                  'alpha-3-code': 'MWI',
                  'continent': 'Africa',
                  'name': 'Malawi',
                  'capital': 'Lilongwe'},
                 {'timezones': ['America/Mexico_City',
                                'America/Cancun',
                                'America/Merida',
                                'America/Monterrey',
                                'America/Mazatlan',
                                'America/Chihuahua',
                                'America/Hermosillo',
                                'America/Tijuana'],
                  'alpha-2-code': 'MX',
                  'alpha-3-code': 'MEX',
                  'continent': 'North America',
                  'name': 'Mexico',
                  'capital': 'Mexico City'},
                 {'timezones': ['Asia/Kuala_Lumpur',
                                'Asia/Kuching'],
                  'alpha-2-code': 'MY',
                  'alpha-3-code': 'MYS',
                  'continent': 'Asia',
                  'name': 'Malaysia',
                  'capital': 'Kuala Lumpur'},
                 {'timezones': ['Africa/Maputo'],
                  'alpha-2-code': 'MZ',
                  'alpha-3-code': 'MOZ',
                  'continent': 'Africa',
                  'name': 'Mozambique',
                  'capital': 'Maputo'},
                 {'timezones': ['Africa/Windhoek'],
                  'alpha-2-code': 'NA',
                  'alpha-3-code': 'NAM',
                  'continent': 'Africa',
                  'name': 'Namibia',
                  'capital': 'Windhoek'},
                 {'timezones': ['Africa/Niamey'],
                  'alpha-2-code': 'NE',
                  'alpha-3-code': 'NER',
                  'continent': 'Africa',
                  'name': 'Niger',
                  'capital': 'Niamey'},
                 {'timezones': ['Africa/Lagos'],
                  'alpha-2-code': 'NG',
                  'alpha-3-code': 'NGA',
                  'continent': 'Africa',
                  'name': 'Nigeria',
                  'capital': 'Abuja'},
                 {'timezones': ['America/Managua'],
                  'alpha-2-code': 'NI',
                  'alpha-3-code': 'NIC',
                  'continent': 'North America',
                  'name': 'Nicaragua',
                  'capital': 'Managua'},
                 {'timezones': ['Europe/Amsterdam'],
                  'alpha-2-code': 'NL',
                  'alpha-3-code': 'NLD',
                  'continent': 'Europe',
                  'name': 'Kingdom of the Netherlands',
                  'capital': 'Amsterdam'},
                 {'timezones': ['Europe/Oslo'],
                  'alpha-2-code': 'NO',
                  'alpha-3-code': 'NOR',
                  'continent': 'Europe',
                  'name': 'Norway',
                  'capital': 'Oslo'},
                 {'timezones': ['Asia/Katmandu'],
                  'alpha-2-code': 'NP',
                  'alpha-3-code': 'NPL',
                  'continent': 'Asia',
                  'name': 'Nepal',
                  'capital': 'Kathmandu'},
                 {'timezones': ['Pacific/Nauru'],
                  'alpha-2-code': 'NR',
                  'alpha-3-code': 'NRU',
                  'continent': 'Oceania',
                  'name': 'Nauru',
                  'capital': 'Yaren'},
                 {'timezones': ['Pacific/Auckland',
                                'Pacific/Chatham'],
                  'alpha-2-code': 'NZ',
                  'alpha-3-code': 'NZL',
                  'continent': 'Oceania',
                  'name': 'New Zealand',
                  'capital': 'Wellington'},
                 {'timezones': ['Asia/Muscat'],
                  'alpha-2-code': 'OM',
                  'alpha-3-code': 'OMN',
                  'continent': 'Asia',
                  'name': 'Oman',
                  'capital': 'Muscat'},
                 {'timezones': ['America/Panama'],
                  'alpha-2-code': 'PA',
                  'alpha-3-code': 'PAN',
                  'continent': 'North America',
                  'name': 'Panama',
                  'capital': 'Panama City'},
                 {'timezones': ['America/Lima'],
                  'alpha-2-code': 'PE',
                  'alpha-3-code': 'PER',
                  'continent': 'South America',
                  'name': 'Peru',
                  'capital': 'Lima'},
                 {'timezones': ['Pacific/Port_Moresby'],
                  'alpha-2-code': 'PG',
                  'alpha-3-code': 'PNG',
                  'continent': 'Oceania',
                  'name': 'Papua New Guinea',
                  'capital': 'Port Moresby'},
                 {'timezones': ['Asia/Manila'],
                  'alpha-2-code': 'PH',
                  'alpha-3-code': 'PHL',
                  'continent': 'Asia',
                  'name': 'Philippines',
                  'capital': 'Manila'},
                 {'timezones': ['Asia/Karachi'],
                  'alpha-2-code': 'PK',
                  'alpha-3-code': 'PAK',
                  'continent': 'Asia',
                  'name': 'Pakistan',
                  'capital': 'Islamabad'},
                 {'timezones': ['Europe/Warsaw'],
                  'alpha-2-code': 'PL',
                  'alpha-3-code': 'POL',
                  'continent': 'Europe',
                  'name': 'Poland',
                  'capital': 'Warsaw'},
                 {'timezones': ['Europe/Lisbon',
                                'Atlantic/Madeira',
                                'Atlantic/Azores'],
                  'alpha-2-code': 'PT',
                  'alpha-3-code': 'PRT',
                  'continent': 'Europe',
                  'name': 'Portugal',
                  'capital': 'Lisbon'},
                 {'timezones': ['Pacific/Palau'],
                  'alpha-2-code': 'PW',
                  'alpha-3-code': 'PLW',
                  'continent': 'Oceania',
                  'name': 'Palau',
                  'capital': 'Ngerulmud'},
                 {'timezones': ['America/Asuncion'],
                  'alpha-2-code': 'PY',
                  'alpha-3-code': 'PRY',
                  'continent': 'South America',
                  'name': 'Paraguay',
                  'capital': 'Asunci\xc3\xb3n'},
                 {'timezones': ['Asia/Qatar'],
                  'alpha-2-code': 'QA',
                  'alpha-3-code': 'QAT',
                  'continent': 'Asia',
                  'name': 'Qatar',
                  'capital': 'Doha'},
                 {'timezones': ['Europe/Bucharest'],
                  'alpha-2-code': 'RO',
                  'alpha-3-code': 'ROU',
                  'continent': 'Europe',
                  'name': 'Romania',
                  'capital': 'Bucharest'},
                 {'timezones': ['Europe/Kaliningrad',
                                'Europe/Moscow',
                                'Europe/Volgograd',
                                'Europe/Samara',
                                'Asia/Yekaterinburg',
                                'Asia/Omsk',
                                'Asia/Novosibirsk',
                                'Asia/Krasnoyarsk',
                                'Asia/Irkutsk',
                                'Asia/Yakutsk',
                                'Asia/Vladivostok',
                                'Asia/Sakhalin',
                                'Asia/Magadan',
                                'Asia/Kamchatka',
                                'Asia/Anadyr'],
                  'alpha-2-code': 'RU',
                  'alpha-3-code': 'RUS',
                  'continent': 'Europe',
                  'name': 'Russia',
                  'capital': 'Moscow'},
                 {'timezones': ['Africa/Kigali'],
                  'alpha-2-code': 'RW',
                  'alpha-3-code': 'RWA',
                  'continent': 'Africa',
                  'name': 'Rwanda',
                  'capital': 'Kigali'},
                 {'timezones': ['Asia/Riyadh'],
                  'alpha-2-code': 'SA',
                  'alpha-3-code': 'SAU',
                  'continent': 'Asia',
                  'name': 'Saudi Arabia',
                  'capital': 'Riyadh'},
                 {'timezones': ['Pacific/Guadalcanal'],
                  'alpha-2-code': 'SB',
                  'alpha-3-code': 'SLB',
                  'continent': 'Oceania',
                  'name': 'Solomon Islands',
                  'capital': 'Honiara'},
                 {'timezones': ['Indian/Mahe'],
                  'alpha-2-code': 'SC',
                  'alpha-3-code': 'SYC',
                  'continent': 'Africa',
                  'name': 'Seychelles',
                  'capital': 'Victoria'},
                 {'timezones': ['Africa/Khartoum'],
                  'alpha-2-code': 'SD',
                  'alpha-3-code': 'SDN',
                  'continent': 'Africa',
                  'name': 'Sudan',
                  'capital': 'Khartoum'},
                 {'timezones': ['Europe/Stockholm'],
                  'alpha-2-code': 'SE',
                  'alpha-3-code': 'SWE',
                  'continent': 'Europe',
                  'name': 'Sweden',
                  'capital': 'Stockholm'},
                 {'timezones': ['Asia/Singapore'],
                  'alpha-2-code': 'SG',
                  'alpha-3-code': 'SGP',
                  'continent': 'Asia',
                  'name': 'Singapore',
                  'capital': 'Singapore'},
                 {'timezones': ['Europe/Ljubljana'],
                  'alpha-2-code': 'SI',
                  'alpha-3-code': 'SVN',
                  'continent': 'Europe',
                  'name': 'Slovenia',
                  'capital': 'Ljubljana'},
                 {'timezones': ['Europe/Bratislava'],
                  'alpha-2-code': 'SK',
                  'alpha-3-code': 'SVK',
                  'continent': 'Europe',
                  'name': 'Slovakia',
                  'capital': 'Bratislava'},
                 {'timezones': ['Africa/Freetown'],
                  'alpha-2-code': 'SL',
                  'alpha-3-code': 'SLE',
                  'continent': 'Africa',
                  'name': 'Sierra Leone',
                  'capital': 'Freetown'},
                 {'timezones': ['Europe/San_Marino'],
                  'alpha-2-code': 'SM',
                  'alpha-3-code': 'SMR',
                  'continent': 'Europe',
                  'name': 'San Marino',
                  'capital': 'San Marino'},
                 {'timezones': ['Africa/Dakar'],
                  'alpha-2-code': 'SN',
                  'alpha-3-code': 'SEN',
                  'continent': 'Africa',
                  'name': 'Senegal',
                  'capital': 'Dakar'},
                 {'timezones': ['Africa/Mogadishu'],
                  'alpha-2-code': 'SO',
                  'alpha-3-code': 'SOM',
                  'continent': 'Africa',
                  'name': 'Somalia',
                  'capital': 'Mogadishu'},
                 {'timezones': ['America/Paramaribo'],
                  'alpha-2-code': 'SR',
                  'alpha-3-code': 'SUR',
                  'continent': 'South America',
                  'name': 'Suriname',
                  'capital': 'Paramaribo'},
                 {'timezones': ['Africa/Sao_Tome'],
                  'alpha-2-code': 'ST',
                  'alpha-3-code': 'STP',
                  'continent': 'Africa',
                  'name': 'S\xc3\xa3o Tom\xc3\xa9 and Pr\xc3\xadncipe',
                  'capital': 'S\xc3\xa3o Tom\xc3\xa9'},
                 {'timezones': ['Asia/Damascus'],
                  'alpha-2-code': 'SY',
                  'alpha-3-code': 'SYR',
                  'continent': 'Asia',
                  'name': 'Syria',
                  'capital': 'Damascus'},
                 {'timezones': ['Africa/Lome'],
                  'alpha-2-code': 'TG',
                  'alpha-3-code': 'TGO',
                  'continent': 'Africa',
                  'name': 'Togo',
                  'capital': 'Lom\xc3\xa9'},
                 {'timezones': ['Asia/Bangkok'],
                  'alpha-2-code': 'TH',
                  'alpha-3-code': 'THA',
                  'continent': 'Asia',
                  'name': 'Thailand',
                  'capital': 'Bangkok'},
                 {'timezones': ['Asia/Dushanbe'],
                  'alpha-2-code': 'TJ',
                  'alpha-3-code': 'TJK',
                  'continent': 'Asia',
                  'name': 'Tajikistan',
                  'capital': 'Dushanbe'},
                 {'timezones': ['Asia/Ashgabat'],
                  'alpha-2-code': 'TM',
                  'alpha-3-code': 'TKM',
                  'continent': 'Asia',
                  'name': 'Turkmenistan',
                  'capital': 'Ashgabat'},
                 {'timezones': ['Africa/Tunis'],
                  'alpha-2-code': 'TN',
                  'alpha-3-code': 'TUN',
                  'continent': 'Africa',
                  'name': 'Tunisia',
                  'capital': 'Tunis'},
                 {'timezones': ['Pacific/Tongatapu'],
                  'alpha-2-code': 'TO',
                  'alpha-3-code': 'TON',
                  'continent': 'Oceania',
                  'name': 'Tonga',
                  'capital': 'Nuku\xca\xbbalofa'},
                 {'timezones': ['Europe/Istanbul'],
                  'alpha-2-code': 'TR',
                  'alpha-3-code': 'TUR',
                  'continent': 'Asia',
                  'name': 'Turkey',
                  'capital': 'Ankara'},
                 {'timezones': ['America/Port_of_Spain'],
                  'alpha-2-code': 'TT',
                  'alpha-3-code': 'TTO',
                  'continent': 'North America',
                  'name': 'Trinidad and Tobago',
                  'capital': 'Port of Spain'},
                 {'timezones': ['Pacific/Funafuti'],
                  'alpha-2-code': 'TV',
                  'alpha-3-code': 'TUV',
                  'continent': 'Oceania',
                  'name': 'Tuvalu',
                  'capital': 'Funafuti'},
                 {'timezones': ['Africa/Dar_es_Salaam'],
                  'alpha-2-code': 'TZ',
                  'alpha-3-code': 'TZA',
                  'continent': 'Africa',
                  'name': 'Tanzania',
                  'capital': 'Dodoma'},
                 {'timezones': ['Europe/Kiev',
                                'Europe/Uzhgorod',
                                'Europe/Zaporozhye',
                                'Europe/Simferopol'],
                  'alpha-2-code': 'UA',
                  'alpha-3-code': 'UKR',
                  'continent': 'Europe',
                  'name': 'Ukraine',
                  'capital': 'Kiev'},
                 {'timezones': ['Africa/Kampala'],
                  'alpha-2-code': 'UG',
                  'alpha-3-code': 'UGA',
                  'continent': 'Africa',
                  'name': 'Uganda',
                  'capital': 'Kampala'},
                 {'timezones': ['America/New_York',
                                'America/Detroit',
                                'America/Kentucky/Louisville',
                                'America/Kentucky/Monticello',
                                'America/Indiana/Indianapolis',
                                'America/Indiana/Marengo',
                                'America/Indiana/Knox',
                                'America/Indiana/Vevay',
                                'America/Chicago',
                                'America/Indiana/Vincennes',
                                'America/Indiana/Petersburg',
                                'America/Menominee',
                                'America/North_Dakota/Center',
                                'America/North_Dakota/New_Salem',
                                'America/Denver',
                                'America/Boise',
                                'America/Shiprock',
                                'America/Phoenix',
                                'America/Los_Angeles',
                                'America/Anchorage',
                                'America/Juneau',
                                'America/Yakutat',
                                'America/Nome',
                                'America/Adak',
                                'Pacific/Honolulu'],
                  'alpha-2-code': 'US',
                  'alpha-3-code': 'USA',
                  'continent': 'North America',
                  'name': 'United States',
                  'capital': 'Washington, D.C.'},
                 {'timezones': ['America/Montevideo'],
                  'alpha-2-code': 'UY',
                  'alpha-3-code': 'URY',
                  'continent': 'South America',
                  'name': 'Uruguay',
                  'capital': 'Montevideo'},
                 {'timezones': ['Asia/Samarkand',
                                'Asia/Tashkent'],
                  'alpha-2-code': 'UZ',
                  'alpha-3-code': 'UZB',
                  'continent': 'Asia',
                  'name': 'Uzbekistan',
                  'capital': 'Tashkent'},
                 {'timezones': ['Europe/Vatican'],
                  'alpha-2-code': 'VA',
                  'alpha-3-code': 'VAT',
                  'continent': 'Europe',
                  'name': 'Vatican City',
                  'capital': 'Vatican City'},
                 {'timezones': ['America/Caracas'],
                  'alpha-2-code': 'VE',
                  'alpha-3-code': 'VEN',
                  'continent': 'South America',
                  'name': 'Venezuela',
                  'capital': 'Caracas'},
                 {'timezones': ['Asia/Saigon'],
                  'alpha-2-code': 'VN',
                  'alpha-3-code': 'VNM',
                  'continent': 'Asia',
                  'name': 'Vietnam',
                  'capital': 'Hanoi'},
                 {'timezones': ['Pacific/Efate'],
                  'alpha-2-code': 'VU',
                  'alpha-3-code': 'VUT',
                  'continent': 'Oceania',
                  'name': 'Vanuatu',
                  'capital': 'Port Vila'},
                 {'timezones': ['Asia/Aden'],
                  'alpha-2-code': 'YE',
                  'alpha-3-code': 'YEM',
                  'continent': 'Asia',
                  'name': 'Yemen',
                  'capital': "Sana'a"},
                 {'timezones': ['Africa/Lusaka'],
                  'alpha-2-code': 'ZM',
                  'alpha-3-code': 'ZMB',
                  'continent': 'Africa',
                  'name': 'Zambia',
                  'capital': 'Lusaka'},
                 {'timezones': ['Africa/Harare'],
                  'alpha-2-code': 'ZW',
                  'alpha-3-code': 'ZWE',
                  'continent': 'Africa',
                  'name': 'Zimbabwe',
                  'capital': 'Harare'},
                 {'timezones': ['Africa/Algiers'],
                  'alpha-2-code': 'DZ',
                  'alpha-3-code': 'DZA',
                  'continent': 'Africa',
                  'name': 'Algeria',
                  'capital': 'Algiers'},
                 {'timezones': ['Europe/Sarajevo'],
                  'alpha-2-code': 'BA',
                  'alpha-3-code': 'BIH',
                  'continent': 'Europe',
                  'name': 'Bosnia and Herzegovina',
                  'capital': 'Sarajevo'},
                 {'timezones': ['Asia/Phnom_Penh'],
                  'alpha-2-code': 'KH',
                  'alpha-3-code': 'KHM',
                  'continent': 'Asia',
                  'name': 'Cambodia',
                  'capital': 'Phnom Penh'},
                 {'timezones': ['Africa/Bangui'],
                  'alpha-2-code': 'CF',
                  'alpha-3-code': 'CAF',
                  'continent': 'Africa',
                  'name': 'Central African Republic',
                  'capital': 'Bangui'},
                 {'timezones': ['Africa/Ndjamena'],
                  'alpha-2-code': 'TD',
                  'alpha-3-code': 'TCD',
                  'continent': 'Africa',
                  'name': 'Chad',
                  'capital': "N'Djamena"},
                 {'timezones': ['Indian/Comoro'],
                  'alpha-2-code': 'KM',
                  'alpha-3-code': 'COM',
                  'continent': 'Africa',
                  'name': 'Comoros',
                  'capital': 'Moroni'},
                 {'timezones': ['Europe/Zagreb'],
                  'alpha-2-code': 'HR',
                  'alpha-3-code': 'HRV',
                  'continent': 'Europe',
                  'name': 'Croatia',
                  'capital': 'Zagreb'},
                 {'timezones': ['Asia/Dili'],
                  'alpha-2-code': 'TL',
                  'alpha-3-code': 'TLS',
                  'continent': 'Asia',
                  'name': 'East Timor',
                  'capital': 'Dili'},
                 {'timezones': ['America/El_Salvador'],
                  'alpha-2-code': 'SV',
                  'alpha-3-code': 'SLV',
                  'continent': 'North America',
                  'name': 'El Salvador',
                  'capital': 'San Salvador'},
                 {'timezones': ['Africa/Malabo'],
                  'alpha-2-code': 'GQ',
                  'alpha-3-code': 'GNQ',
                  'continent': 'Africa',
                  'name': 'Equatorial Guinea',
                  'capital': 'Malabo'},
                 {'timezones': ['America/Grenada'],
                  'alpha-2-code': 'GD',
                  'alpha-3-code': 'GRD',
                  'continent': 'North America',
                  'name': 'Grenada',
                  'capital': "St. George's"},
                 {'timezones': ['Asia/Almaty',
                                'Asia/Qyzylorda',
                                'Asia/Aqtobe',
                                'Asia/Aqtau',
                                'Asia/Oral'],
                  'alpha-2-code': 'KZ',
                  'alpha-3-code': 'KAZ',
                  'continent': 'Asia',
                  'name': 'Kazakhstan',
                  'capital': 'Astana'},
                 {'timezones': ['Asia/Vientiane'],
                  'alpha-2-code': 'LA',
                  'alpha-3-code': 'LAO',
                  'continent': 'Asia',
                  'name': 'Laos',
                  'capital': 'Vientiane'},
                 {'timezones': ['Pacific/Truk',
                                'Pacific/Ponape',
                                'Pacific/Kosrae'],
                  'alpha-2-code': 'FM',
                  'alpha-3-code': 'FSM',
                  'continent': 'Oceania',
                  'name': 'Federated States of Micronesia',
                  'capital': 'Palikir'},
                 {'timezones': ['Europe/Chisinau'],
                  'alpha-2-code': 'MD',
                  'alpha-3-code': 'MDA',
                  'continent': 'Europe',
                  'name': 'Moldova',
                  'capital': 'Chi\xc5\x9fin\xc4\x83u'},
                 {'timezones': ['Europe/Monaco'],
                  'alpha-2-code': 'MC',
                  'alpha-3-code': 'MCO',
                  'continent': 'Europe',
                  'name': 'Monaco',
                  'capital': 'Monaco'},
                 {'timezones': ['Europe/Podgorica'],
                  'alpha-2-code': 'ME',
                  'alpha-3-code': 'MNE',
                  'continent': 'Europe',
                  'name': 'Montenegro',
                  'capital': 'Podgorica'},
                 {'timezones': ['Africa/Casablanca'],
                  'alpha-2-code': 'MA',
                  'alpha-3-code': 'MAR',
                  'continent': 'Africa',
                  'name': 'Morocco',
                  'capital': 'Rabat'},
                 {'timezones': ['America/St_Kitts'],
                  'alpha-2-code': 'KN',
                  'alpha-3-code': 'KNA',
                  'continent': 'North America',
                  'name': 'Saint Kitts and Nevis',
                  'capital': 'Basseterre'},
                 {'timezones': ['America/St_Lucia'],
                  'alpha-2-code': 'LC',
                  'alpha-3-code': 'LCA',
                  'continent': 'North America',
                  'name': 'Saint Lucia',
                  'capital': 'Castries'},
                 {'timezones': ['America/St_Vincent'],
                  'alpha-2-code': 'VC',
                  'alpha-3-code': 'VCT',
                  'continent': 'North America',
                  'name': 'Saint Vincent and the Grenadines',
                  'capital': 'Kingstown'},
                 {'timezones': ['Pacific/Apia'],
                  'alpha-2-code': 'WS',
                  'alpha-3-code': 'WSM',
                  'continent': 'Oceania',
                  'name': 'Samoa',
                  'capital': 'Apia'},
                 {'timezones': ['Europe/Belgrade'],
                  'alpha-2-code': 'RS',
                  'alpha-3-code': 'SRB',
                  'continent': 'Europe',
                  'name': 'Serbia',
                  'capital': 'Belgrade'},
                 {'timezones': ['Africa/Johannesburg'],
                  'alpha-2-code': 'ZA',
                  'alpha-3-code': 'ZAF',
                  'continent': 'Africa',
                  'name': 'South Africa',
                  'capital': 'Pretoria'},
                 {'timezones': ['Europe/Madrid',
                                'Africa/Ceuta',
                                'Atlantic/Canary'],
                  'alpha-2-code': 'ES',
                  'alpha-3-code': 'ESP',
                  'continent': 'Europe',
                  'name': 'Spain',
                  'capital': 'Madrid'},
                 {'timezones': ['Asia/Colombo'],
                  'alpha-2-code': 'LK',
                  'alpha-3-code': 'LKA',
                  'continent': 'Asia',
                  'name': 'Sri Lanka',
                  'capital': 'Sri Jayewardenepura Kotte'},
                 {'timezones': ['Africa/Mbabane'],
                  'alpha-2-code': 'SZ',
                  'alpha-3-code': 'SWZ',
                  'continent': 'Africa',
                  'name': 'Swaziland',
                  'capital': 'Mbabane'},
                 {'timezones': ['Europe/Zurich'],
                  'alpha-2-code': 'CH',
                  'alpha-3-code': 'CHE',
                  'continent': 'Europe',
                  'name': 'Switzerland',
                  'capital': 'Bern'},
                 {'timezones': ['Asia/Dubai'],
                  'alpha-2-code': 'AE',
                  'alpha-3-code': 'ARE',
                  'continent': 'Asia',
                  'name': 'United Arab Emirates',
                  'capital': 'Abu Dhabi'},
                 {'timezones': ['Europe/London'],
                  'alpha-2-code': 'GB',
                  'alpha-3-code': 'GBR',
                  'continent': 'Europe',
                  'name': 'United Kingdom',
                  'capital': 'London'},
                 ]

    regex = re.compile(timedelta_pattern)

    def unix_time(self, end_datetime=None, start_datetime=None):
        """
        Get a timestamp between January 1, 1970 and now, unless passed
        explicit start_datetime or end_datetime values.
        :example 1061306726
        """
        start_datetime = self._parse_start_datetime(start_datetime)
        end_datetime = self._parse_end_datetime(end_datetime)
        return self.generator.random.randint(start_datetime, end_datetime)

    def time_delta(self, end_datetime=None):
        """
        Get a timedelta object
        """
        start_datetime = self._parse_start_datetime('now')
        end_datetime = self._parse_end_datetime(end_datetime)
        seconds = end_datetime - start_datetime

        ts = self.generator.random.randint(*sorted([0, seconds]))
        return timedelta(seconds=ts)

    def date_time(self, tzinfo=None, end_datetime=None):
        """
        Get a datetime object for a date between January 1, 1970 and now
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example DateTime('2005-08-16 20:39:21')
        :return datetime
        """
        # NOTE: On windows, the lowest value you can get from windows is 86400
        #       on the first day. Known python issue:
        #       https://bugs.python.org/issue30684
        return datetime(1970, 1, 1, tzinfo=tzinfo) + \
            timedelta(seconds=self.unix_time(end_datetime=end_datetime))

    def date_time_ad(self, tzinfo=None, end_datetime=None, start_datetime=None):
        """
        Get a datetime object for a date between January 1, 001 and now
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example DateTime('1265-03-22 21:15:52')
        :return datetime
        """

        # 1970-01-01 00:00:00 UTC minus 62135596800 seconds is
        # 0001-01-01 00:00:00 UTC.  Since _parse_end_datetime() is used
        # elsewhere where a default value of 0 is expected, we can't
        # simply change that class method to use this magic number as a
        # default value when None is provided.

        start_time = -62135596800 if start_datetime is None else self._parse_start_datetime(start_datetime)
        end_datetime = self._parse_end_datetime(end_datetime)

        ts = self.generator.random.randint(start_time, end_datetime)
        # NOTE: using datetime.fromtimestamp(ts) directly will raise
        #       a "ValueError: timestamp out of range for platform time_t"
        #       on some platforms due to system C functions;
        #       see http://stackoverflow.com/a/10588133/2315612
        # NOTE: On windows, the lowest value you can get from windows is 86400
        #       on the first day. Known python issue:
        #       https://bugs.python.org/issue30684
        return datetime(1970, 1, 1, tzinfo=tzinfo) + timedelta(seconds=ts)

    def iso8601(self, tzinfo=None, end_datetime=None):
        """
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example '2003-10-21T16:05:52+0000'
        """
        return self.date_time(tzinfo, end_datetime=end_datetime).isoformat()

    def date(self, pattern='%Y-%m-%d', end_datetime=None):
        """
        Get a date string between January 1, 1970 and now
        :param pattern format
        :example '2008-11-27'
        """
        return self.date_time(end_datetime=end_datetime).strftime(pattern)

    def date_object(self, end_datetime=None):
        """
        Get a date object between January 1, 1970 and now
        :example datetime.date(2016, 9, 20)
        """
        return self.date_time(end_datetime=end_datetime).date()

    def time(self, pattern='%H:%M:%S', end_datetime=None):
        """
        Get a time string (24h format by default)
        :param pattern format
        :example '15:02:34'
        """
        return self.date_time(
            end_datetime=end_datetime).time().strftime(pattern)

    def time_object(self, end_datetime=None):
        """
        Get a time object
        :example datetime.time(15, 56, 56, 772876)
        """
        return self.date_time(end_datetime=end_datetime).time()

    @classmethod
    def _parse_start_datetime(cls, value):
        if value is None:
            return 0

        return cls._parse_date_time(value)

    @classmethod
    def _parse_end_datetime(cls, value):
        if value is None:
            return int(time())

        return cls._parse_date_time(value)

    @classmethod
    def _parse_date_string(cls, value):
        parts = cls.regex.match(value)
        if not parts:
            raise ParseError("Can't parse date string `{}`.".format(value))
        parts = parts.groupdict()
        time_params = {}
        for (name_, param_) in parts.items():
            if param_:
                time_params[name_] = int(param_)

        if 'years' in time_params:
            if 'days' not in time_params:
                time_params['days'] = 0
            time_params['days'] += 365.24 * time_params.pop('years')
        if 'months' in time_params:
            if 'days' not in time_params:
                time_params['days'] = 0
            time_params['days'] += 30.42 * time_params.pop('months')

        if not time_params:
            raise ParseError("Can't parse date string `{}`.".format(value))
        return time_params

    @classmethod
    def _parse_timedelta(cls, value):
        if isinstance(value, timedelta):
            return value.total_seconds()
        if is_string(value):
            time_params = cls._parse_date_string(value)
            return timedelta(**time_params).total_seconds()
        if isinstance(value, (int, float)):
            return value
        raise ParseError("Invalid format for timedelta '{0}'".format(value))

    @classmethod
    def _parse_date_time(cls, value, tzinfo=None):
        if isinstance(value, (datetime, date, real_datetime, real_date)):
            return datetime_to_timestamp(value)
        now = datetime.now(tzinfo)
        if isinstance(value, timedelta):
            return datetime_to_timestamp(now + value)
        if is_string(value):
            if value == 'now':
                return datetime_to_timestamp(datetime.now(tzinfo))
            time_params = cls._parse_date_string(value)
            return datetime_to_timestamp(now + timedelta(**time_params))
        if isinstance(value, int):
            return datetime_to_timestamp(now + timedelta(value))
        raise ParseError("Invalid format for date '{0}'".format(value))

    @classmethod
    def _parse_date(cls, value):
        if isinstance(value, (datetime, real_datetime)):
            return value.date()
        elif isinstance(value, (date, real_date)):
            return value
        today = date.today()
        if isinstance(value, timedelta):
            return today + value
        if is_string(value):
            if value in ('today', 'now'):
                return today
            time_params = cls._parse_date_string(value)
            return today + timedelta(**time_params)
        if isinstance(value, int):
            return today + timedelta(value)
        raise ParseError("Invalid format for date '{0}'".format(value))

    def date_time_between(self, start_date='-30y', end_date='now', tzinfo=None):
        """
        Get a DateTime object based on a random date between two given dates.
        Accepts date strings that can be recognized by strtotime().

        :param start_date Defaults to 30 years ago
        :param end_date Defaults to "now"
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example DateTime('1999-02-02 11:42:52')
        :return DateTime
        """
        start_date = self._parse_date_time(start_date, tzinfo=tzinfo)
        end_date = self._parse_date_time(end_date, tzinfo=tzinfo)
        if end_date - start_date <= 1:
            ts = start_date + self.generator.random.random()
        else:
            ts = self.generator.random.randint(start_date, end_date)
        if tzinfo is None:
            return datetime(1970, 1, 1, tzinfo=tzinfo) + timedelta(seconds=ts)
        else:
            return (
                datetime(1970, 1, 1, tzinfo=tzutc()) + timedelta(seconds=ts)
            ).astimezone(tzinfo)

    def date_between(self, start_date='-30y', end_date='today'):
        """
        Get a Date object based on a random date between two given dates.
        Accepts date strings that can be recognized by strtotime().

        :param start_date Defaults to 30 years ago
        :param end_date Defaults to "today"
        :example Date('1999-02-02')
        :return Date
        """

        start_date = self._parse_date(start_date)
        end_date = self._parse_date(end_date)
        return self.date_between_dates(date_start=start_date, date_end=end_date)

    def future_datetime(self, end_date='+30d', tzinfo=None):
        """
        Get a DateTime object based on a random date between 1 second form now
        and a given date.
        Accepts date strings that can be recognized by strtotime().

        :param end_date Defaults to "+30d"
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example DateTime('1999-02-02 11:42:52')
        :return DateTime
        """
        return self.date_time_between(
            start_date='+1s', end_date=end_date, tzinfo=tzinfo,
        )

    def future_date(self, end_date='+30d', tzinfo=None):
        """
        Get a Date object based on a random date between 1 day from now and a
        given date.
        Accepts date strings that can be recognized by strtotime().

        :param end_date Defaults to "+30d"
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example DateTime('1999-02-02 11:42:52')
        :return DateTime
        """
        return self.date_between(start_date='+1d', end_date=end_date)

    def past_datetime(self, start_date='-30d', tzinfo=None):
        """
        Get a DateTime object based on a random date between a given date and 1
        second ago.
        Accepts date strings that can be recognized by strtotime().

        :param start_date Defaults to "-30d"
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example DateTime('1999-02-02 11:42:52')
        :return DateTime
        """
        return self.date_time_between(
            start_date=start_date, end_date='-1s', tzinfo=tzinfo,
        )

    def past_date(self, start_date='-30d', tzinfo=None):
        """
        Get a Date object based on a random date between a given date and 1 day
        ago.
        Accepts date strings that can be recognized by strtotime().

        :param start_date Defaults to "-30d"
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example DateTime('1999-02-02 11:42:52')
        :return DateTime
        """
        return self.date_between(start_date=start_date, end_date='-1d')

    def date_time_between_dates(
            self,
            datetime_start=None,
            datetime_end=None,
            tzinfo=None):
        """
        Takes two DateTime objects and returns a random datetime between the two
        given datetimes.
        Accepts DateTime objects.

        :param datetime_start: DateTime
        :param datetime_end: DateTime
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example DateTime('1999-02-02 11:42:52')
        :return DateTime
        """
        if datetime_start is None:
            datetime_start = datetime.now(tzinfo)

        if datetime_end is None:
            datetime_end = datetime.now(tzinfo)

        timestamp = self.generator.random.randint(
            datetime_to_timestamp(datetime_start),
            datetime_to_timestamp(datetime_end),
        )
        try:
            if tzinfo is None:
                pick = datetime.fromtimestamp(timestamp, tzlocal())
                pick = pick.astimezone(tzutc()).replace(tzinfo=None)
            else:
                pick = datetime.fromtimestamp(timestamp, tzinfo)
        except OverflowError:
            raise OverflowError(
                "You specified an end date with a timestamp bigger than the maximum allowed on this"
                " system. Please specify an earlier date.",
            )
        return pick

    def date_between_dates(self, date_start=None, date_end=None):
        """
        Takes two Date objects and returns a random date between the two given dates.
        Accepts Date or Datetime objects

        :param date_start: Date
        :param date_end: Date
        :return Date
        """
        return self.date_time_between_dates(date_start, date_end).date()

    def date_time_this_century(
            self,
            before_now=True,
            after_now=False,
            tzinfo=None):
        """
        Gets a DateTime object for the current century.

        :param before_now: include days in current century before today
        :param after_now: include days in current century after today
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example DateTime('2012-04-04 11:02:02')
        :return DateTime
        """
        now = datetime.now(tzinfo)
        this_century_start = datetime(
            now.year - (now.year % 100), 1, 1, tzinfo=tzinfo)
        next_century_start = datetime(
            min(this_century_start.year + 100, MAXYEAR), 1, 1, tzinfo=tzinfo)

        if before_now and after_now:
            return self.date_time_between_dates(
                this_century_start, next_century_start, tzinfo)
        elif not before_now and after_now:
            return self.date_time_between_dates(now, next_century_start, tzinfo)
        elif not after_now and before_now:
            return self.date_time_between_dates(this_century_start, now, tzinfo)
        else:
            return now

    def date_time_this_decade(
            self,
            before_now=True,
            after_now=False,
            tzinfo=None):
        """
        Gets a DateTime object for the decade year.

        :param before_now: include days in current decade before today
        :param after_now: include days in current decade after today
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example DateTime('2012-04-04 11:02:02')
        :return DateTime
        """
        now = datetime.now(tzinfo)
        this_decade_start = datetime(
            now.year - (now.year % 10), 1, 1, tzinfo=tzinfo)
        next_decade_start = datetime(
            min(this_decade_start.year + 10, MAXYEAR), 1, 1, tzinfo=tzinfo)

        if before_now and after_now:
            return self.date_time_between_dates(
                this_decade_start, next_decade_start, tzinfo)
        elif not before_now and after_now:
            return self.date_time_between_dates(now, next_decade_start, tzinfo)
        elif not after_now and before_now:
            return self.date_time_between_dates(this_decade_start, now, tzinfo)
        else:
            return now

    def date_time_this_year(
            self,
            before_now=True,
            after_now=False,
            tzinfo=None):
        """
        Gets a DateTime object for the current year.

        :param before_now: include days in current year before today
        :param after_now: include days in current year after today
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example DateTime('2012-04-04 11:02:02')
        :return DateTime
        """
        now = datetime.now(tzinfo)
        this_year_start = now.replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        next_year_start = datetime(now.year + 1, 1, 1, tzinfo=tzinfo)

        if before_now and after_now:
            return self.date_time_between_dates(
                this_year_start, next_year_start, tzinfo)
        elif not before_now and after_now:
            return self.date_time_between_dates(now, next_year_start, tzinfo)
        elif not after_now and before_now:
            return self.date_time_between_dates(this_year_start, now, tzinfo)
        else:
            return now

    def date_time_this_month(
            self,
            before_now=True,
            after_now=False,
            tzinfo=None):
        """
        Gets a DateTime object for the current month.

        :param before_now: include days in current month before today
        :param after_now: include days in current month after today
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example DateTime('2012-04-04 11:02:02')
        :return DateTime
        """
        now = datetime.now(tzinfo)
        this_month_start = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)

        next_month_start = this_month_start + \
            relativedelta.relativedelta(months=1)
        if before_now and after_now:
            return self.date_time_between_dates(
                this_month_start, next_month_start, tzinfo)
        elif not before_now and after_now:
            return self.date_time_between_dates(now, next_month_start, tzinfo)
        elif not after_now and before_now:
            return self.date_time_between_dates(this_month_start, now, tzinfo)
        else:
            return now

    def date_this_century(self, before_today=True, after_today=False):
        """
        Gets a Date object for the current century.

        :param before_today: include days in current century before today
        :param after_today: include days in current century after today
        :example Date('2012-04-04')
        :return Date
        """
        today = date.today()
        this_century_start = date(today.year - (today.year % 100), 1, 1)
        next_century_start = date(this_century_start.year + 100, 1, 1)

        if before_today and after_today:
            return self.date_between_dates(
                this_century_start, next_century_start)
        elif not before_today and after_today:
            return self.date_between_dates(today, next_century_start)
        elif not after_today and before_today:
            return self.date_between_dates(this_century_start, today)
        else:
            return today

    def date_this_decade(self, before_today=True, after_today=False):
        """
        Gets a Date object for the decade year.

        :param before_today: include days in current decade before today
        :param after_today: include days in current decade after today
        :example Date('2012-04-04')
        :return Date
        """
        today = date.today()
        this_decade_start = date(today.year - (today.year % 10), 1, 1)
        next_decade_start = date(this_decade_start.year + 10, 1, 1)

        if before_today and after_today:
            return self.date_between_dates(this_decade_start, next_decade_start)
        elif not before_today and after_today:
            return self.date_between_dates(today, next_decade_start)
        elif not after_today and before_today:
            return self.date_between_dates(this_decade_start, today)
        else:
            return today

    def date_this_year(self, before_today=True, after_today=False):
        """
        Gets a Date object for the current year.

        :param before_today: include days in current year before today
        :param after_today: include days in current year after today
        :example Date('2012-04-04')
        :return Date
        """
        today = date.today()
        this_year_start = today.replace(month=1, day=1)
        next_year_start = date(today.year + 1, 1, 1)

        if before_today and after_today:
            return self.date_between_dates(this_year_start, next_year_start)
        elif not before_today and after_today:
            return self.date_between_dates(today, next_year_start)
        elif not after_today and before_today:
            return self.date_between_dates(this_year_start, today)
        else:
            return today

    def date_this_month(self, before_today=True, after_today=False):
        """
        Gets a Date object for the current month.

        :param before_today: include days in current month before today
        :param after_today: include days in current month after today
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example DateTime('2012-04-04 11:02:02')
        :return DateTime
        """
        today = date.today()
        this_month_start = today.replace(day=1)

        next_month_start = this_month_start + \
            relativedelta.relativedelta(months=1)
        if before_today and after_today:
            return self.date_between_dates(this_month_start, next_month_start)
        elif not before_today and after_today:
            return self.date_between_dates(today, next_month_start)
        elif not after_today and before_today:
            return self.date_between_dates(this_month_start, today)
        else:
            return today

    def time_series(
            self,
            start_date='-30d',
            end_date='now',
            precision=None,
            distrib=None,
            tzinfo=None):
        """
        Returns a generator yielding tuples of ``(<datetime>, <value>)``.

        The data points will start at ``start_date``, and be at every time interval specified by
        ``precision``.
        ``distrib`` is a callable that accepts ``<datetime>`` and returns ``<value>``

        """
        start_date = self._parse_date_time(start_date, tzinfo=tzinfo)
        end_date = self._parse_date_time(end_date, tzinfo=tzinfo)

        if end_date < start_date:
            raise ValueError("`end_date` must be greater than `start_date`.")

        if precision is None:
            precision = (end_date - start_date) / 30

        precision = self._parse_timedelta(precision)
        if distrib is None:
            def distrib(dt): return self.generator.random.uniform(0, precision)  # noqa

        if not callable(distrib):
            raise ValueError(
                "`distrib` must be a callable. Got {} instead.".format(distrib))

        datapoint = start_date
        while datapoint < end_date:
            dt = timestamp_to_datetime(datapoint, tzinfo)
            datapoint += precision
            yield (dt, distrib(dt))

    def am_pm(self):
        return self.date('%p')

    def day_of_month(self):
        return self.date('%d')

    def day_of_week(self):
        return self.date('%A')

    def month(self):
        return self.date('%m')

    def month_name(self):
        return self.date('%B')

    def year(self):
        return self.date('%Y')

    def century(self):
        """
        :example 'XVII'
        """
        return self.random_element(self.centuries)

    def timezone(self):
        return self.generator.random.choice(
            self.random_element(self.countries)['timezones'])

    def date_of_birth(self, tzinfo=None, minimum_age=0, maximum_age=115):
        """
        Generate a random date of birth represented as a Date object,
        constrained by optional miminimum_age and maximum_age
        parameters.

        :param tzinfo Defaults to None.
        :param minimum_age Defaults to 0.
        :param maximum_age Defaults to 115.

        :example Date('1979-02-02')
        :return Date
        """

        if not isinstance(minimum_age, int):
            raise TypeError("minimum_age must be an integer.")

        if not isinstance(maximum_age, int):
            raise TypeError("maximum_age must be an integer.")

        if (maximum_age < 0):
            raise ValueError("maximum_age must be greater than or equal to zero.")

        if (minimum_age < 0):
            raise ValueError("minimum_age must be greater than or equal to zero.")

        if (minimum_age > maximum_age):
            raise ValueError("minimum_age must be less than or equal to maximum_age.")

        # In order to return the full range of possible dates of birth, add one
        # year to the potential age cap and subtract one day if we land on the
        # boundary.

        now = datetime.now(tzinfo).date()
        start_date = now.replace(year=now.year - (maximum_age+1))
        end_date = now.replace(year=now.year - minimum_age)

        dob = self.date_time_ad(tzinfo=tzinfo, start_datetime=start_date, end_datetime=end_date).date()

        return dob if dob != start_date else dob + timedelta(days=1)
