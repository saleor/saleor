# coding=utf-8


from __future__ import unicode_literals
from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):

    # https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Russia
    license_plate_letters = ('A', 'B', 'E', 'M', 'Н', 'О', 'Р', 'С', 'Т', 'У', 'Х')

    license_plate_suffix = (
        # Republic of Adygea
        '01',
        # Republic of Bashkortostan
        '02', '102',
        # Republic of Buryatia
        '03',
        # Altai Republic
        '04',
        # Republic of Dagestan
        '05',
        # Republic of Ingushetia
        '06',
        # Kabardino-Balkar Republic
        '07',
        # Republic of Kalmykia
        '08',
        # Karachay-Cherkess Republic
        '09',
        # Republic of Karelia
        '10',
        # Komi Republic
        '11',
        # Mari El Republic
        '12',
        # Republic of Mordovia
        '13', '113',
        # Sakha Republic
        '14',
        # Republic of North Ossetia–Alania
        '15',
        # Republic of Tatarstan
        '16', '116', '716',
        # Tuva Republic
        '17',
        # Udmurt Republic
        '18',
        # Republic of Khakassia
        '19',
        # Chechen Republic
        '20', '95',
        # Chuvash Republic
        '21', '121',
        # Altai Krai
        '22',
        # Krasnodar Krai
        '23', '93', '123',
        # Krasnoyarsk Krai
        '24', '84', '88', '124',
        # Primorsky Krai
        '25', '125',
        # Stavropol Krai
        '26', '126',
        # Khabarovsk Krai
        '27',
        # Amur Oblast
        '28',
        # Arkhangelsk Oblast
        '29',
        # Astrakhan Oblast
        '30',
        # Belgorod Oblast
        '31',
        # Bryansk Oblast
        '32',
        # Vladimir Oblast
        '33',
        # Volgograd Oblast
        '34', '134',
        # Vologda Oblast
        '35',
        # Voronezh Oblast
        '36', '136',
        # Ivanovo Oblast
        '37',
        # Irkutsk Oblast
        '38', '85', '38',
        # Kaliningrad Oblast
        '39', '91',
        # Kaluga Oblast
        '40',
        # Kamchatka Krai
        '41', '82',
        # Kemerovo Oblast
        '42', '142',
        # Kirov Oblast
        '43',
        # Kostroma Oblast
        '44',
        # Kurgan Oblast
        '45',
        # Kursk Oblast
        '46',
        # Leningrad Oblast
        '47',
        # Lipetsk Oblast
        '48',
        # Magadan Oblast
        '49',
        # Moscow Oblast
        '50', '90', '150', '190', '750',
        # Murmansk Oblast
        '51',
        # Nizhny Novgorod Oblast
        '52', '152',
        # Novgorod Oblast
        '53',
        # Novosibirsk Oblast
        '54', '154',
        # Omsk Oblast
        '55',
        # Orenburg Oblast
        '56',
        # Oryol Oblast
        '57',
        # Penza Oblast
        '58',
        # Perm Krai
        '59', '81', '159',
        # Pskov Oblast
        '60',
        # Rostov Oblast
        '61', '161',
        # Ryazan Oblast
        '62',
        # Samara Oblast
        '63', '163', '763',
        # Saratov Oblast
        '64', '164',
        # Sakhalin Oblast
        '65',
        # Sverdlovsk Oblast
        '66', '96', '196',
        # Smolensk Oblast
        '67',
        # Tambov Oblast
        '68',
        # Tver Oblast
        '69',
        # Tomsk Oblast
        '70',
        # Tula Oblast
        '71',
        # Tyumen Oblast
        '72',
        # Ulyanovsk Oblast
        '73', '173',
        # Chelyabinsk Oblast
        '74', '174',
        # Zabaykalsky Krai
        '75', '80',
        # Yaroslavl Oblast
        '76',
        # Moscow
        '77', '97', '99', '177', '197', '199', '777', '799',
        # St. Petersburg
        '78', '98', '178', '198',
        # Jewish Autonomous Oblast
        '79',
        # Agin-Buryat Okrug / "Former Buryat Autonomous District of Aginskoye"
        '80',
        # Komi-Permyak Okrug / "Former Komi-Permyak Autonomous District"
        '81',
        # Republic of Crimea / De jure part of Ukraine as Autonomous Republic. Annexed by Russia in 2014.
        '82',
        # Koryak Okrug / "Former Koryak Autonomous District"
        '82',
        # Nenets Autonomous Okrug (Nenetsia)
        '83',
        # Taymyr Autonomous Okrug / "Former Taymyr (Dolgan-Nenets) Autonomous District"
        '84',
        # Ust-Orda Buryat Okrug / "Former Buryat Autonomous District of Ust-Ordynskoy"
        '85',
        # Khanty-Mansi Autonomous Okrug
        '86', '186',
        # Chukotka Autonomous Okrug
        '87',
        # Evenk Autonomous Okrug / "Former Evenk Autonomous District"
        '88',
        # Yamalo-Nenets Autonomous Okrug
        '89',
        # Sevastopol / De jure part of Ukraine as City with special status. Annexed by Russia in 2014.
        '92',
        # Territories outside of the Russian Federation,
        # served by the bodies of internal affairs of the Russian Federation, such as Baikonur
        '94',
    )

    license_plate_number = (
        '##%'
    )

    def license_plate(self):
        return self.random_element(self.license_plate_letters) + \
               self.numerify(self.generator.parse(self.license_plate_number)) + \
               self.random_element(self.license_plate_letters) + \
               self.random_element(self.license_plate_letters) + \
               self.random_element(self.license_plate_suffix)
