# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as CompanyProvider


class Provider(CompanyProvider):

    formats = (
        '{{last_name}} {{company_suffix}}',
        '{{last_name}} & {{last_name}}',
        '{{company_prefix}} {{last_name}}',
        '{{large_company}}',
    )

    company_prefixes = (
        'Stichting', 'Koninklijke', 'Royal',
    )

    company_suffixes = (
        'BV', 'NV', 'Groep',
    )

    # Source: https://www.mt.nl/management/reputatie/mt-500-2018-de-lijst/559930
    large_companies = (
        'Shell', 'Coolblue', 'ASML', 'Ahold', 'Tata Steel', 'KLM', 'Bol.com', 'BP Nederland', 'De Efteling', 'Eneco',
        'De Persgroep', 'ING', 'Royal HaskoningDHV', 'Randstad', 'Google', 'Ikea', 'Rockwool', 'BAM', 'Achmea',
        'Damen Shipyard', 'ABN Amro', 'Remeha Group', 'TenneT', 'Coca-Cola', 'Van Leeuwen Buizen', 'Wavin', 'Rabobank',
        'AkzoNobel', 'Arcadis', 'AFAS', 'Cisco', 'DAF Trucks', 'DHL', 'Hanos', 'Boon Edam', 'BMW Nederland',
        'The Greenery', 'Dutch Flower Group', 'Koninklijke Mosa', 'Yacht', 'Rituals', 'Microsoft', 'Esso',
        '3W Vastgoed', 'Deloitte', 'Corio', 'Voortman Steel Group', 'Agrifirm', 'Makro Nederland',
        'Nederlandse Publieke Omroep', 'De Alliantie', 'Heijmans', 'McDonalds', 'ANWB', 'Mediamarkt', 'Kruidvat'
        'Van Merksteijn Steel', 'Dura Vermeer', 'Alliander', 'Unilever', 'Enexis', 'Berenschot', 'Jumbo',
        'Technische Unie', 'Havenbedrijf Rotterdam', 'Ballast Nedam', 'RTL Nederland', 'Talpa Media',
        'Blauwhoed Vastgoed', 'DSM', 'Ymere', 'Witteveen+Bos', 'NS', 'Action', 'FloraHolland', 'Heineken', 'Nuon', 'EY',
        'Dow Benelux', 'Bavaria', 'Schiphol', 'Holland Casino', 'Binck bank', 'BDO', 'HEMA', 'Alphabet Nederland',
        'Croon Elektrotechniek', 'ASR Vastgoed ontwikkeling', 'PwC', 'Mammoet', 'KEMA', 'IBM', 'A.S. Watson',
        'KPMG', 'VodafoneZiggo', 'YoungCapital', 'Triodos Bank', 'Aviko', 'AgruniekRijnvallei', 'Heerema', 'Accenture',
        'Aegon', 'NXP', 'Breman Installatiegroep', 'Movares Groep', 'Q-Park', 'FleuraMetz', 'Sanoma',
        'Bakker Logistiek', 'VDL Group', 'Bayer', 'Boskalis', 'Nutreco', 'Dell', 'Brunel', 'Exact', 'Manpower',
        'Essent', 'Canon', 'ONVZ Zorgverzekeraar', 'Telegraaf Media Group', 'Nationale Nederlanden', 'Andus Group',
        'Den Braven Group', 'ADP', 'ASR', 'ArboNed', 'Plieger', 'De Heus Diervoeders', 'USG People', 'Bidvest Deli XL',
        'Apollo Vredestein', 'Tempo-Team', 'Trespa', 'Janssen Biologics', 'Starbucks', 'PostNL', 'Vanderlande',
        'FrieslandCampina', 'Constellium', 'Huisman', 'Abbott', 'Koninklijke Boom Uitgevers', 'Bosch Rexroth', 'BASF',
        'Audax', 'VolkerWessels', 'Hunkemöller', 'Athlon Car Lease', 'DSW Zorgverzekeraar', 'Mars',
        'De Brauw Blackstone Westbroek', 'NDC Mediagroep', 'Bluewater', 'Stedin', 'Feenstra',
        'Wuppermann Staal Nederland', 'Kramp', 'SABIC', 'Iv-Groep', 'Bejo Zaden', 'Wolters Kluwer', 'Nyrstar holding',
        'Adecco', 'Tauw', 'Robeco', 'Eriks', 'Allianz Nederland Groep', 'Driessen', 'Burger King', 'Lekkerland',
        'Van Lanschot', 'Brocacef', 'Bureau Veritas', 'Relx', 'Pathé Bioscopen', 'Bosal',
        'Ardagh Group', 'Maandag', 'Inalfa', 'Atradius', 'Capgemini', 'Greenchoice', 'Q8 (Kuwait Petroleum Europe)',
        'ASM International', 'Van der Valk', 'Delta Lloyd', 'GlaxoSmithKline', 'ABB',
        'Fabory, a Grainger company', 'Veen Bosch & Keuning Uitgeversgroep', 'CZ', 'Plus', 'RET Rotterdam',
        'Loyens & Loeff', 'Holland Trading', 'Archer Daniels Midland Nederland', 'Ten Brinke', 'NAM', 'DAS',
        'Samsung Electronics Benelux', 'Koopman International', 'TUI', 'Lannoo Meulenhoff', 'AC Restaurants',
        'Stage Entertainment', 'Acer', 'HDI Global SE', 'Detailresult', 'Nestle', 'GVB Amsterdam', 'Dekamarkt', 'Dirk',
        'MSD', 'Arriva', 'Baker Tilly Berk', 'SBM Offshore', 'TomTom', 'Fujifilm', 'B&S', 'BCC', 'Gasunie',
        'Oracle Nederland', 'Astellas Pharma', 'SKF', 'Woningstichting Eigen Haard', 'Rijk Zwaan', 'Chubb', 'Fugro',
        'Total', 'Rochdale', 'ASVB', 'Atos', 'Acomo', 'KPN', 'Van Drie Group', 'Olympia uitzendbureau',
        'Bacardi Nederland', 'JMW Horeca Uitzendbureau', 'Warner Bros/Eyeworks', 'Aalberts Industries', 'SNS Bank',
        'Amtrada Holding', 'VGZ', 'Grolsch', 'Office Depot', 'De Rijke Group', 'Bovemij Verzekeringsgroep',
        'Coop Nederland', 'Eaton Industries', 'ASN', 'Yara Sluiskil', 'HSF Logistics', 'Fokker', 'Deutsche Bank',
        'Sweco', 'Univé Groep', 'Koninklijke Wagenborg', 'Strukton', 'Conclusion', 'Philips', 'In Person',
        'Fluor', 'Vroegop-Windig', 'ArboUnie', 'Centraal Boekhuis', 'Siemens', 'Connexxion', 'Fujitsu', 'Consolid',
        'AVR Afvalverwerking', 'Brabant Alucast', 'Centric', 'Havensteder', 'Novartis', 'Booking.com', 'Menzis',
        'Frankort & Koning Groep', 'Jan de Rijk', 'Brand Loyalty Group', 'Ohra Verzekeringen', 'Terberg Group',
        'Cloetta', 'Holland & Barrett', 'Enza Zaden', 'VION', 'Woonzorg Nederland',
        'T-Mobile', 'Crucell', 'NautaDutilh', 'BNP Paribas', 'NIBC Bank', 'VastNed', 'CCV Holland',
        'IHC Merwede', 'Neways', 'NSI N.V.', 'Deen', 'Accor', 'HTM', 'ITM Group', 'Ordina', 'Dümmen Orange', 'Optiver',
        'Zara', 'L\'Oreal Nederland B.V.', 'Vinci Energies', 'Suit Supply Topco', 'Sita', 'Vos Logistics',
        'Altran', 'St. Clair', 'BESI', 'Fiat Chrysler Automobiles', 'UPS', 'Jacobs', 'Emté', 'TBI', 'De Bijenkorf',
        'Aldi Nederland', 'Van Wijnen', 'Vitens', 'De Goudse Verzekeringen', 'SBS Broadcasting',
        'Sandd', 'Omron', 'Sogeti', 'Alfa Accountants & Adviseurs', 'Harvey Nash', 'Stork', 'Glencore Grain',
        'Meijburg & Co', 'Honeywell', 'Meyn', 'Ericsson Telecommunicatie', 'Hurks', 'Mitsubishi', 'GGN',
        'CGI Nederland', 'Staples Nederland', 'Denkavit International', 'Ecorys', 'Rexel Nederland',
        'A. Hakpark', 'DuPont Nederland', 'CBRE Group', 'Bolsius', 'Marel', 'Metro',
        'Flynth Adviseurs en Accountants', 'Kropman Installatietechniek', 'Kuijpers', 'Medtronic', 'Cefetra',
        'Simon Loos', 'Citadel Enterprises', 'Intergamma', 'Ceva Logistics', 'Beter Bed', 'Subway', 'Gamma', 'Karwei'
        'Varo Energy', 'APM Terminals', 'Center Parcs', 'Brenntag Nederland', 'NFI', 'Hoogvliet',
        'Van Gansewinkel', 'Nedap', 'Blokker', 'Perfetti Van Melle', 'Vestia', 'Kuehne + Nagel Logistics',
        'Rensa Group', 'NTS Group', 'Joh. Mourik & Co. Holding', 'Mercedes-Benz', 'DIT Personeel', 'Verkade',
        'Hametha', 'Vopak', 'IFF', 'Pearle', 'Mainfreight', 'De Jong & Laan', 'DSV', 'P4People', 'Mazars', 'Cargill',
        'Ten Brinke Groep', 'Alewijnse', 'Agio Cigars', 'Peter Appel Transport', 'Syngenta', 'Avery Dennison',
        'Accon AVM', 'Vitol', 'Vermaat Groep', 'BMC', 'Alcatel-Lucent', 'Maxeda DIY', 'Equens',
        'Van Gelder Groep', 'Emerson Electric Nederland', 'Bakkersland', 'Specsavers', 'E.On', 'Landal Greenparks',
        'IMC Trading', 'Barentz Group', 'Epson', 'Raet', 'Van Oord', 'Thomas Cook Nederland', 'SDU uitgevers',
        'Nedschroef', 'Linde Gas', 'Ewals Cargo Care', 'Theodoor Gilissen', 'TMF Group', 'Cornelis Vrolijk',
        'Jan Linders Supermarkten', 'SIF group', 'BT Nederland', 'Kinepolis', 'Pink Elephant',
        'General Motors Nederland', 'Carlson Wagonlit', 'Bruna', 'Docdata', 'Schenk Tanktransport', 'WPG', 'Peak-IT',
        'Martinair', 'Reesink', 'Elopak Nederland', 'Fagron N.V.', 'OVG Groep', 'Ford Nederland', 'Multi Corporation',
        'Simac', 'Primark', 'Tech Data Nederland', 'Vleesgroothandel Zandbergen', 'Raben Group', 'Farm Frites',
        'Libéma', 'Caldic', 'Portaal', 'Syntus', 'Jacobs DE', 'Stena Line', 'The Phone House', 'Interfood Group',
        'Thales', 'Teva Pharmaceuticals', 'RFS Holland', 'Aebi Schmidt Nederland',
        'Rockwell Automation Nederland', 'Engie Services', 'Hendrix Genetics', 'Qbuzz', 'Unica',
        '2SistersFoodGroup', 'Ziut', 'Munckhof Groep', 'Spar Holding', 'Samskip', 'Continental Bakeries', 'Sligro',
        'Merck', 'Foot Locker Europe', 'Unit4', 'PepsiCo', 'Sulzer', 'Tebodin', 'Value8', 'Boels',
        'DKG Groep', 'Bruynzeel Keukens', 'Janssen de Jong Groep', 'ProRail', 'Solid Professionals', 'Hermes Partners',
    )

    def large_company(self):
        """
        :example: 'Bol.com'
        """
        return self.random_element(self.large_companies)

    def company_prefix(self):
        """
        :example 'Stichting'
        """
        return self.random_element(self.company_prefixes)
