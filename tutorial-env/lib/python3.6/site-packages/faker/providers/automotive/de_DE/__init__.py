# coding=utf-8


from __future__ import unicode_literals
from .. import Provider as AutomotiveProvider
import string


class Provider(AutomotiveProvider):

    # http://berlin.de/daten/liste-der-kfz-kennzeichen/kfz-kennz-d.csv
    license_plate_prefix = (
        'A', 'AA', 'AB', 'ABI', 'ABG', 'AC', 'AE', 'AIC', 'AK', 'AM', 'AN', 'AÖ', 'AP', 'AS', 'AUR', 'AW', 'AZ', 'B',
        'BA', 'BAD', 'BAR', 'BB', 'BC', 'BD', 'BGL', 'BI', 'BIR', 'BIT', 'BK', 'BL', 'BLK', 'BM', 'BN', 'BO', 'BOR',
        'BOT', 'BP', 'BRA', 'BRB', 'BS', 'BT', 'BTF', 'BÜS', 'BW', 'BWL', 'BYL', 'BZ', 'C', 'CB', 'CE', 'CHA', 'CO',
        'COC', 'COE', 'CUX', 'CW', 'D', 'DA', 'DAH', 'DAN', 'DAU', 'DBR', 'DD', 'DE', 'DEG', 'DEL', 'DGF', 'DH', 'DL',
        'DLG', 'DN', 'Do', 'DON', 'DU', 'DÜW', 'E', 'EA', 'EB', 'EBE', 'ED', 'EE', 'EF', 'EI', 'EIC', 'EL', 'EM', 'EMD',
        'EMS', 'EN', 'ER', 'ERB', 'ERH', 'ERZ', 'ES', 'ESW', 'EU', 'F', 'FB', 'FD', 'FDS', 'FF', 'FFB', 'FG', 'FL',
        'FN', 'FO', 'FR', 'FRG', 'FRI', 'FS', 'FT', 'FÜ', 'G', 'GAP', 'GE', 'GER', 'GF', 'GG', 'GI', 'GL', 'GM', 'GÖ',
        'GP', 'GR', 'GRZ', 'GS', 'GT', 'GTH', 'GÜ', 'GZ', 'H', 'HA', 'HAL', 'HAM', 'HAS', 'HB', 'HBN', 'HD', 'HDH',
        'HE', 'HEF', 'HEI', 'HEL', 'HER', 'HF', 'HG', 'HGW', 'HH', 'HI', 'HL', 'HM', 'HN', 'HO', 'HOL', 'HOM', 'HP',
        'HR', 'HRO', 'HS', 'HSK', 'HST', 'HU', 'HVL', 'HWI', 'HX', 'HZ', 'IGB', 'IK', 'IN', 'IZ', 'J', 'JL', 'K', 'KA',
        'KB', 'KC', 'KE', 'KEH', 'KF', 'KG', 'KH', 'KI', 'KIB', 'KL', 'KLE', 'KN', 'KO', 'KR', 'KS', 'KT', 'KU', 'KÜN',
        'KUS', 'KYF', 'L', 'LA', 'LAU', 'LB', 'LD', 'LDK', 'LDS', 'LER', 'LEV', 'LG', 'LI', 'LIF', 'LIP', 'LL', 'LM',
        'LÖ', 'LOS', 'LRO', 'LSA', 'LSN', 'LU', 'LWL', 'M', 'MA', 'MB', 'MD', 'ME', 'MEI', 'MG', 'MI', 'MIL', 'MK',
        'MKK', 'MM', 'MN', 'MOL', 'MOS', 'MR', 'MS', 'MSH', 'MSP', 'MST', 'MTK', 'MÜ', 'MÜR', 'MVL', 'MYK', 'MZ', 'MZG',
        'N', 'NB', 'ND', 'NDH', 'NE', 'NEA', 'NES', 'NEW', 'NF', 'NI', 'NK', 'NL', 'NM', 'NMS', 'NOH', 'NOM', 'NR',
        'NU', 'NVP', 'NW', 'NWM', 'OA', 'OAL', 'OB', 'OD', 'OE', 'OF', 'OG', 'OH', 'OHA', 'OHV', 'OHZ', 'OL', 'OPR',
        'OS', 'OSL', 'OVP', 'P', 'PA', 'PAF', 'PAN', 'PB', 'PCH', 'PE', 'PF', 'PI', 'PIR', 'PLÖ', 'PM', 'PR', 'PS', 'R',
        'RA', 'RD', 'RE', 'REG', 'RO', 'ROS', 'ROW', 'RP', 'RPL', 'RS', 'RT', 'RÜD', 'RÜG', 'RV', 'RW', 'RZ', 'S',
        'SAD', 'SAL', 'SAW', 'SB', 'SC', 'SDL', 'SE', 'SG', 'SH', 'SHA', 'SHG', 'SHK', 'SHL', 'SI', 'SIG', 'SIM', 'SK',
        'SL', 'SLF', 'SLK', 'SLS', 'SM', 'SN', 'SO', 'SOK', 'SÖM', 'SON', 'SP', 'SPN', 'SR', 'ST', 'STA', 'STD', 'SU',
        'SÜW', 'SW', 'SZ', 'TDO', 'TBB', 'TF', 'TG', 'THL', 'THW', 'TIR', 'TÖL', 'TR', 'TS', 'TÜ', 'TUT', 'UE', 'UL',
        'UM', 'UN', 'V', 'VB', 'VEC', 'VER', 'VIE', 'VK', 'VR', 'VS', 'W', 'WAF', 'WAK', 'WB', 'WE', 'WEN', 'WES', 'WF',
        'WHV', 'WI', 'WIL', 'WL', 'WM', 'WN', 'WND', 'WO', 'WOB', 'WST', 'WT', 'WTM', 'WÜ', 'WUG', 'WUN', 'WW', 'WZ',
        'Y', 'Z', 'ZW',
    )

    license_plate_suffix = (
        '-??-%@@@',
        '-?-%@@@',
    )

    def license_plate(self):
        return self.random_element(self.license_plate_prefix) + \
               self.lexify(self.numerify(self.random_element(self.license_plate_suffix)), string.ascii_uppercase)
