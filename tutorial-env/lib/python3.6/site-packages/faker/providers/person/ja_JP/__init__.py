# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as PersonProvider


class Provider(PersonProvider):
    formats_female = (
        '{{last_name}} {{first_name_female}}',
    )

    formats_male = (
        '{{last_name}} {{first_name_male}}',
    )

    formats = formats_male + formats_female

    first_names_female = (
        '明美',
        'あすか',
        '香織',
        '加奈',
        'くみ子',
        'さゆり',
        '知実',
        '千代',
        '直子',
        '七夏',
        '花子',
        '春香',
        '真綾',
        '舞',
        '美加子',
        '幹',
        '桃子',
        '結衣',
        '裕美子',
        '陽子',
        '里佳',
    )

    first_names_male = (
        '晃',
        '篤司',
        '治',
        '和也',
        '京助',
        '健一',
        '修平',
        '翔太',
        '淳',
        '聡太郎',
        '太一',
        '太郎',
        '拓真',
        '翼',
        '智也',
        '直樹',
        '直人',
        '英樹',
        '浩',
        '学',
        '充',
        '稔',
        '裕樹',
        '裕太',
        '康弘',
        '陽一',
        '洋介',
        '亮介',
        '涼平',
        '零',
    )

    first_names = first_names_male + first_names_female

    last_names = (
        '青田', '青山', '石田', '井高', '伊藤', '井上', '宇野', '江古田', '大垣',
        '加藤', '加納', '喜嶋', '木村', '桐山', '工藤', '小泉', '小林', '近藤',
        '斉藤', '坂本', '佐々木', '佐藤', '笹田', '鈴木', '杉山',
        '高橋', '田中', '田辺', '津田',
        '中島', '中村', '渚', '中津川', '西之園', '野村',
        '原田', '浜田', '廣川', '藤本',
        '松本', '三宅', '宮沢', '村山',
        '山岸', '山口', '山田', '山本', '吉田', '吉本',
        '若松', '渡辺',
    )

    kana_formats = (
        '{{last_kana_name}} {{first_kana_name_female}}',
        '{{last_kana_name}} {{first_kana_name_male}}',
    )

    first_kana_names_female = (
        'アキラ', 'アケミ', 'アスカ',
        'カオリ', 'カナ', 'クミコ',
        'サユリ',
        'チヨ', 'ツバサ', 'トモミ',
        'ナオコ', 'ナナカ',
        'ハナコ', 'ハルカ',
        'マアヤ', 'マイ', 'ミキ', 'モモコ',
        'ユイ', 'ヨウコ', 'ユミコ',
        'レイ', 'リカ',
    )

    first_kana_names_male = (
        'アキラ', 'アツシ', 'オサム',
        'キョウスケ', 'ケンイチ',
        'ジュン', 'ソウタロウ',
        'タイチ', 'タクマ', 'タロウ', 'ツバサ', 'トモヤ',
        'ナオキ', 'ナオト',
        'ヒデキ', 'ヒロシ',
        'マナブ', 'ミツル', 'ミノル', 'ヒロキ',
        'ユウタ', 'ヤスヒロ', 'ヨウイチ', 'ヨウスケ',
        'リョウスケ', 'リョウヘイ',
    )

    first_kana_names = first_kana_names_male + first_kana_names_female

    last_kana_names = (
        'アオタ', 'アオヤマ', 'イシダ', 'イダカ', 'イトウ', 'ウノ', 'エコダ', 'オオガキ',
        'カノウ', 'カノウ', 'キジマ', 'キムラ', 'キリヤマ', 'クドウ', 'コイズミ', 'コバヤシ', 'コンドウ',
        'サイトウ', 'サカモト', 'ササキ', 'サトウ', 'ササダ', 'スズキ', 'スギヤマ',
        'タカハシ', 'タナカ', 'タナベ', 'ツダ', 'ツチヤ',
        'ナカジマ', 'ナカムラ', 'ナギサ', 'ナカツガワ', 'ニシノソノ', 'ノムラ',
        'ハラダ', 'ハマダ', 'ヒロカワ', 'フジモト',
        'マツモト', 'ミヤケ', 'ミヤザワ', 'ムラヤマ',
        'ヤマギシ', 'ヤマグチ', 'ヤマダ', 'ヤマモト', 'ヨシダ', 'ヨシモト',
        'ワカマツ', 'ワタナベ',
    )

    romanized_formats = (
        '{{first_romanized_name_female}} {{last_romanized_name}}',
        '{{first_romanized_name_male}} {{last_romanized_name}}',
    )

    first_romanized_names_female = (
        'Akira', 'Akemi', 'Asuka',
        'Kaori', 'Kana', 'Kumiko',
        'Sayuri',
        'Chiyo', 'Tsubasa', 'Tomomi',
        'Naoko', 'Nanaka',
        'Hanako', 'Haruka',
        'Maaya', 'Mai', 'Miki', 'Momoko',
        'Yui', 'Yoko', 'Yumiko',
        'Rei', 'Rika',
    )

    first_romanized_names_male = (
        'Akira', 'Atsushi', 'Osamu',
        'Kyosuke', 'Kenichi',
        'Jun', 'Sotaro',
        'Taichi', 'Takuma', 'Taro', 'Tsubasa', 'Tomoya',
        'Naoki', 'Naoto'
        'Hideki', 'Hiroshi',
        'Manabu', 'Mituru', 'Minoru', 'Hiroki',
        'Yuta', 'Yasuhiro', 'Yoichi', 'Yosuke',
        'Ryosuke', 'Ryohei',
    )

    first_romanized_names = first_romanized_names_male + first_romanized_names_female

    last_romanized_names = (
        'Aota',
        'Aoyama',
        'Ishida',
        'Idaka',
        'Ito',
        'Uno',
        'Ekoda',
        'Ogaki',
        'Kato',
        'Kano',
        'Kijima',
        'Kimura',
        'Kiriyama',
        'Kudo',
        'Koizumi',
        'Kobayashi',
        'Kondo',
        'Saito',
        'Sakamoto',
        'Sasaki',
        'Sato',
        'Sasada',
        'Suzuki',
        'Sugiyama',
        'Takahashi',
        'Tanaka',
        'Tanabe',
        'Tsuda',
        'Tsuchiya',
        'Nakajima',
        'Nakamura',
        'Nagisa',
        'Nakatsugawa',
        'Nishinosono',
        'Nomura',
        'Harada',
        'Hamada',
        'Hirokawa',
        'Fujimoto',
        'Matsumoto',
        'Miyake',
        'Miyagawa',
        'Murayama',
        'Yamagishi',
        'Yamaguchi',
        'Yamada',
        'Yamamoto',
        'Yoshida',
        'Yoshimoto',
        'Wakamatsu',
        'Watanabe',
    )

    def kana_name(self):
        '''
        @example 'アオタ アキラ'
        '''
        pattern = self.random_element(self.kana_formats)
        return self.generator.parse(pattern)

    def first_kana_name(self):
        '''
        @example 'アキラ'
        '''
        return self.random_element(self.first_kana_names)

    def first_kana_name_female(self):
        return self.random_element(self.first_kana_names_female)

    def first_kana_name_male(self):
        return self.random_element(self.first_kana_names_male)

    def last_kana_name(self):
        '''
        @example 'アオタ'
        '''
        return self.random_element(self.last_kana_names)

    def romanized_name(self):
        '''
        @example 'Akira Aota'
        '''
        pattern = self.random_element(self.romanized_formats)
        return self.generator.parse(pattern)

    def first_romanized_name(self):
        '''
        @example 'Akira'
        '''
        return self.random_element(self.first_romanized_names)

    def first_romanized_name_female(self):
        return self.random_element(self.first_romanized_names_female)

    def first_romanized_name_male(self):
        return self.random_element(self.first_romanized_names_male)

    def last_romanized_name(self):
        '''
        @example 'Aota'
        '''
        return self.random_element(self.last_romanized_names)
