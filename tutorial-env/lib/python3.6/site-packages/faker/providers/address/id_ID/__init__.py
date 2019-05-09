# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as AddressProvider


class Provider(AddressProvider):

    building_number_formats = ('###', '##', '#')

    city_formats = ('{{city_name}}',)

    postcode_formats = ('#####',)

    street_name_formats = (
        '{{street_prefix_short}} {{street}}',
        '{{street_prefix_long}} {{street}}',
    )

    street_address_formats = (
        '{{street_name}} No. {{building_number}}',
    )

    address_formats = (
        '{{street_address}}\n{{city}}, {{state}} {{postcode}}',
        '{{street_address}}\n{{city}}, {{state_abbr}} {{postcode}}',
    )

    # From
    # http://elibrary.dephub.go.id/elibrary/media/catalog/0010-021500000000135/swf/618/Lampiran%20E%20Data%20Bandung.pdf
    # https://www.surabaya.go.id/id/info-penting/47601/daftar-nama-jalan-dan-status-ja
    # https://www.streetdirectory.com/indonesia/jakarta/asia_travel/street/popular/
    streets = (
        'Abdul Muis', 'Antapani Lama', 'Asia Afrika', 'Astana Anyar', 'BKR',
        'Cihampelas', 'Cikapayang', 'Cikutra Barat', 'Cikutra Timur',
        'Ciumbuleuit', 'Ciwastra', 'Dipatiukur', 'Dipenogoro', 'Dr. Djunjunan',
        'Gardujati', 'Gedebage Selatan', 'Gegerkalong Hilir',
        'HOS. Cokroaminoto', 'Ir. H. Djuanda', 'Jakarta', 'Jamika',
        'Jend. A. Yani', 'Jend. Sudirman', 'K.H. Wahid Hasyim', 'Kebonjati',
        'Kiaracondong', 'Laswi', 'Lembong', 'Merdeka', 'Moch. Ramdan',
        'Moch. Toha', 'Pacuan Kuda', 'Pasir Koja', 'Pasirkoja', 'Pasteur',
        'Pelajar Pejuang', 'Peta', 'PHH. Mustofa', 'Rajawali Barat',
        'Rajawali Timur', 'Raya Setiabudhi', 'Raya Ujungberung', 'Rumah Sakit',
        'Sadang Serang', 'Sentot Alibasa', 'Setiabudhi', 'Siliwangi',
        'Soekarno Hatta', 'Sukabumi', 'Sukajadi', 'Suniaraja', 'Surapati',
        'Tubagus Ismail', 'Veteran', 'W.R. Supratman', 'Bangka Raya', 'Cempaka',
        'Cihampelas', 'Erlangga', 'Rawamangun', 'Waringin', 'Ronggowarsito',
        'Rajiman', 'Yos Sudarso', 'S. Parman', 'Monginsidi', 'M.T Haryono',
        'Ahmad Dahlan', 'Jayawijaya', 'R.E Martadinata', 'M.H Thamrin',
        'Stasiun Wonokromo', 'Ahmad Yani', 'Joyoboyo', 'Indragiri', 'Kutai',
        'Kutisari Selatan', 'Rungkut Industri', 'Kendalsari', 'Wonoayu',
        'Medokan Ayu', 'KH Amin Jasuta', 'H.J Maemunah', 'Suryakencana',
        'Kapten Muslihat', 'Otto Iskandardinata', 'Tebet Barat Dalam',
    )

    street_prefixes_long = (
        'Jalan', 'Gang',
    )

    street_prefixes_short = (
        'Jl.', 'Gg.',
    )

    # From
    # https://id.wikipedia.org/wiki/Daftar_kabupaten_dan_kota_di_Indonesia#Daftar_kota
    cities = (
        'Ambon', 'Balikpapan', 'Banda Aceh', 'Bandar Lampung', 'Bandung',
        'Banjar', 'Banjarbaru', 'Banjarmasin', 'Batam', 'Batu', 'Bau-Bau',
        'Bekasi', 'Bengkulu', 'Bima', 'Binjai', 'Bitung', 'Blitar', 'Bogor',
        'Bontang', 'Bukittinggi', 'Cilegon', 'Cimahi', 'Cirebon', 'Denpasar',
        'Depok', 'Dumai', 'Gorontalo', 'Jambi', 'Jayapura', 'Kediri', 'Kendari',
        'Kota Administrasi Jakarta Barat', 'Kota Administrasi Jakarta Pusat',
        'Kota Administrasi Jakarta Selatan', 'Kota Administrasi Jakarta Timur',
        'Kota Administrasi Jakarta Utara', 'Kotamobagu', 'Kupang', 'Langsa',
        'Lhokseumawe', 'Lubuklinggau', 'Madiun', 'Magelang', 'Makassar',
        'Malang', 'Manado', 'Mataram', 'Medan', 'Metro', 'Meulaboh',
        'Mojokerto', 'Padang', 'Padang Sidempuan', 'Padangpanjang', 'Pagaralam',
        'Palangkaraya', 'Palembang', 'Palopo', 'Palu', 'Pangkalpinang',
        'Parepare', 'Pariaman', 'Pasuruan', 'Payakumbuh', 'Pekalongan',
        'Pekanbaru', 'Pematangsiantar', 'Pontianak', 'Prabumulih',
        'Probolinggo', 'Purwokerto', 'Sabang', 'Salatiga', 'Samarinda',
        'Sawahlunto', 'Semarang', 'Serang', 'Sibolga', 'Singkawang', 'Solok',
        'Sorong', 'Subulussalam', 'Sukabumi', 'Sungai Penuh', 'Surabaya',
        'Surakarta', 'Tangerang', 'Tangerang Selatan', 'Tanjungbalai',
        'Tanjungpinang', 'Tarakan', 'Tasikmalaya', 'Tebingtinggi', 'Tegal',
        'Ternate', 'Tidore Kepulauan', 'Tomohon', 'Tual', 'Yogyakarta',
    )

    # From https://id.wikipedia.org/wiki/Daftar_provinsi_di_Indonesia
    states = (
        'Aceh', 'Bali', 'Banten', 'Bengkulu', 'DI Yogyakarta', 'DKI Jakarta',
        'Gorontalo', 'Jambi', 'Jawa Barat', 'Jawa Tengah', 'Jawa Timur',
        'Kalimantan Barat', 'Kalimantan Selatan', 'Kalimantan Tengah',
        'Kalimantan Timur', 'Kalimantan Utara', 'Kepulauan Bangka Belitung',
        'Kepulauan Riau', 'Lampung', 'Maluku', 'Maluku Utara',
        'Nusa Tenggara Barat', 'Nusa Tenggara Timur', 'Papua', 'Papua Barat',
        'Riau', 'Sulawesi Barat', 'Sulawesi Selatan', 'Sulawesi Tengah',
        'Sulawesi Tenggara', 'Sulawesi Utara', 'Sumatera Barat',
        'Sumatera Selatan', 'Sumatera Utara',
    )

    # https://id.wikipedia.org/wiki/Daftar_provinsi_di_Indonesia
    states_abbr = (
        'AC', 'BA', 'BT', 'BE', 'YO', 'JK', 'GO',
        'JA', 'JB', 'JT', 'JI', 'KB', 'KS', 'KT',
        'KI', 'KU', 'BB', 'KR', 'LA', 'MA', 'MU',
        'NB', 'NT', 'PA', 'PB', 'RI', 'SR', 'SN', 'ST',
        'SG', 'SU', 'SB', 'SS', 'SU',
    )

    # From https://id.wikipedia.org/wiki/Daftar_negara-negara_di_dunia
    countries = (
        'Afganistan', 'Afrika Selatan', 'Afrika Tengah', 'Albania', 'Aljazair',
        'Amerika Serikat', 'Andorra', 'Angola', 'Antigua dan Barbuda',
        'Arab Saudi', 'Argentina', 'Armenia', 'Australia', 'Austria',
        'Azerbaijan', 'Bahama', 'Bahrain', 'Bangladesh', 'Barbados', 'Belanda',
        'Belarus', 'Belgia', 'Belize', 'Benin', 'Bhutan', 'Bolivia',
        'Bosnia dan Herzegovina', 'Botswana', 'Brasil', 'Britania Raya',
        'Brunei', 'Bulgaria', 'Burkina Faso', 'Burundi', 'Ceko', 'Chad',
        'Chili', 'Denmark', 'Djibouti', 'Dominika', 'Ekuador', 'El Salvador',
        'Eritrea', 'Estonia', 'Ethiopia', 'Federasi Mikronesia', 'Fiji',
        'Filipina', 'Finlandia', 'Gabon', 'Gambia', 'Georgia', 'Ghana',
        'Grenada', 'Guatemala', 'Guinea', 'Guinea Khatulistiwa',
        'Guinea-Bissau', 'Guyana', 'Haiti', 'Honduras', 'Hongaria', 'India',
        'Indonesia', 'Irak', 'Iran', 'Islandia', 'Israel', 'Italia', 'Jamaika',
        'Jepang', 'Jerman', 'Kamboja', 'Kamerun', 'Kanada', 'Kazakhstan',
        'Kenya', 'Kepulauan Marshall', 'Kepulauan Solomon', 'Kirgizstan',
        'Kiribati', 'Kolombia', 'Komoro', 'Korea Selatan', 'Korea Utara',
        'Kosta Rika', 'Kroasia', 'Kuba', 'Kuwait', 'Laos', 'Latvia', 'Lebanon',
        'Lesotho', 'Liberia', 'Libya', 'Liechtenstein', 'Lituania',
        'Luksemburg', 'Madagaskar', 'Maladewa', 'Malawi', 'Malaysia', 'Mali',
        'Malta', 'Maroko', 'Mauritania', 'Mauritius', 'Meksiko', 'Mesir',
        'Moldova', 'Monako', 'Mongolia', 'Montenegro', 'Mozambik', 'Myanmar',
        'Namibia', 'Nauru', 'Nepal', 'Niger', 'Nigeria', 'Nikaragua',
        'Norwegia', 'Oman', 'Pakistan', 'Palau', 'Panama', 'Pantai Gading',
        'Papua Nugini', 'Paraguay', 'Perancis', 'Peru', 'Polandia', 'Portugal',
        'Qatar', 'Republik Demokratik Kongo', 'Republik Dominika',
        'Republik Irlandia', 'Republik Kongo', 'Republik Makedonia',
        'Republik Rakyat Tiongkok', 'Rumania', 'Rusia', 'Rwanda',
        'Saint Kitts dan Nevis', 'Saint Lucia', 'Saint Vincent dan Grenadine',
        'Samoa', 'San Marino', 'São Tomé dan Príncipe', 'Selandia Baru',
        'Senegal', 'Serbia', 'Seychelles', 'Sierra Leone', 'Singapura',
        'Siprus', 'Slovenia', 'Slowakia', 'Somalia', 'Spanyol', 'Sri Lanka',
        'Sudan', 'Sudan Selatan', 'Suriah', 'Suriname', 'Swaziland', 'Swedia',
        'Swiss', 'Tajikistan', 'Tanjung Verde', 'Tanzania', 'Thailand',
        'Timor Leste', 'Togo', 'Tonga', 'Trinidad dan Tobago', 'Tunisia',
        'Turki', 'Turkmenistan', 'Tuvalu', 'Uganda', 'Ukraina',
        'Uni Emirat Arab', 'Uruguay', 'Uzbekistan', 'Vanuatu', 'Vatikan',
        'Venezuela', 'Vietnam', 'Yaman', 'Yordania', 'Yunani', 'Zambia',
        'Zimbabwe',
    )

    def street(self):
        return self.random_element(self.streets)

    def street_prefix_short(self):
        return self.random_element(self.street_prefixes_short)

    def street_prefix_long(self):
        return self.random_element(self.street_prefixes_long)

    def city_name(self):
        return self.random_element(self.cities)

    def state(self):
        return self.random_element(self.states)

    def state_abbr(self):
        return self.random_element(self.states_abbr)

    def country(self):
        return self.random_element(self.countries)
