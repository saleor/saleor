# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as AddressProvider


class Provider(AddressProvider):
    """
    Korean Address Provider
    =======================

    Korea has two address and postal code system.

    Address
    -------

    - Address based on land parcel numbers
      (지번 주소, OLD, but someone use consistently)
    - Address based on road names and building numbers (도로명 주소, NEW)

    :meth:`land_address` generate Address based on land parcel numbers and
    :meth:`road_address` generate Address based on road names and building
    numbers.

    Postal code
    -----------

    - Old postal code (6-digit, OLD and dead)
    - New postal code (5-digit, New)

    :meth:`old_postal_code` and :meth:`postcode` generate old 6-digit code
    and :meth:`postal_code` generate newer 5-digit code.

    Reference
    ---------

    - `Official Confirmation Prividing that Old and New Addresses are Identical`__
      (warn: cert error)

    __ https://www.juso.go.kr/addridentity/AddrIdentityHelp.htm

    """

    building_suffixes = (
        '빌라',
        '아파트',
        '연립',
        '마을',
        '타운',
        '타워',
    )
    road_suffixes = ('로', '길', '거리', '가')
    town_suffixes = ('동', '리', '마을')
    postcode_formats = ('###-###',)
    new_postal_code_formats = ('#####',)
    metropolitan_cities = (
        '서울특별시',
        '부산광역시',
        '대구광역시',
        '인천광역시',
        '광주광역시',
        '대전광역시',
        '울산광역시',
        '세종특별자치시',
    )
    provinces = (
        '경기도',
        '강원도',
        '충청북도',
        '충청남도',
        '전라북도',
        '전라남도',
        '경상북도',
        '경상남도',
        '제주특별자치도',
    )
    cities = (
        '파주시',
        '수원시',
        '수원시 권선구',
        '수원시 팔달구',
        '수원시 영통구',
        '성남시',
        '성남시 수정구',
        '성남시 중원구',
        '화성시',
        '성남시 분당구',
        '안양시',
        '안양시 만안구',
        '안양시 동안구',
        '부천시',
        '부천시 원미구',
        '부천시 소사구',
        '부천시 오정구',
        '광명시',
        '평택시',
        '이천시',
        '동두천시',
        '안산시',
        '안산시 상록구',
        '안산시 단원구',
        '안성시',
        '고양시',
        '고양시 덕양구',
        '고양시 일산동구',
        '고양시 일산서구',
        '과천시',
        '구리시',
        '남양주시',
        '오산시',
        '시흥시',
        '군포시',
        '의왕시',
        '하남시',
        '김포시',
        '용인시',
        '용인시 처인구',
        '용인시 기흥구',
        '용인시 수지구',
        '연천군',
        '가평군',
        '양평군',
        '광주시',
        '포천시',
        '양주시',
        '수원시 장안구',
        '의정부시',
        '여주시',
    )
    road_names = (
        '압구정',
        '도산대',
        '학동',
        '봉은사',
        '테헤란',
        '역삼',
        '논현',
        '언주',
        '강남대',
        '양재천',
        '삼성',
        '영동대',
        '개포',
        '선릉',
        '반포대',
        '서초중앙',
        '서초대',
        '잠실',
        '석촌호수',
        '백제고분',
        '가락',
        '오금',
    )
    boroughs = (
        '종로구',
        '중구',
        '용산구',
        '성동구',
        '광진구',
        '동대문구',
        '중랑구',
        '성북구',
        '강북구',
        '도봉구',
        '노원구',
        '은평구',
        '서대문구',
        '마포구',
        '양천구',
        '강서구',
        '구로구',
        '금천구',
        '영등포구',
        '동작구',
        '관악구',
        '서초구',
        '강남구',
        '송파구',
        '강동구',
        '동구',
        '서구',
        '남구',
        '북구',
    )
    countries = ('가나', '가봉', '가이아나', '감비아', '과테말라', '그레나다', '그리스', '기니', '기니비사우',
                 '나미비아', '나우루', '나이지리아', '남수단', '남아프리카 공화국', '네덜란드 왕국', '네팔',
                 '노르웨이', '뉴질랜드', '니제르', '니카라과', '대한민국', '덴마크', '도미니카 공화국',
                 '도미니카 연방', '독일', '동티모르', '라오스', '라이베리아', '라트비아', '러시아', '레바논',
                 '레소토', '루마니아', '룩셈부르크', '르완다', '리비아', '리투아니아', '리히텐슈타인',
                 '마다가스카르', '마셜 제도', '마케도니아 공화국', '말라위', '말레이시아', '말리', '멕시코',
                 '모나코', '모로코', '모리셔스', '모리타니', '모잠비크', '몬테네그로', '몰도바', '몰디브',
                 '몰타', '몽골', '미국', '미얀마', '미크로네시아 연방', '바누아투', '바레인', '바베이도스',
                 '바하마', '방글라데시', '베냉', '베네수엘라', '베트남', '벨기에', '벨라루스', '벨리즈',
                 '보스니아 헤르체고비나', '보츠와나', '볼리비아', '부룬디', '부르키나파소', '부탄', '불가리아',
                 '브라질', '브루나이', '사모아', '사우디아라비아', '산마리노', '상투메 프린시페', '세네갈',
                 '세르비아', '세이셸', '세인트루시아', '세인트빈센트 그레나딘', '세인트키츠 네비스',
                 '소말리아', '솔로몬 제도', '수단', '수리남', '스리랑카', '스와질란드', '스웨덴', '스위스',
                 '스페인', '슬로바키아', '슬로베니아', '시리아', '시에라리온 공화국', '싱가포르',
                 '아랍에미리트', '아르메니아', '아르헨티나', '아이슬란드', '아이티', '아일랜드',
                 '아제르바이잔', '아프가니스탄', '안도라', '알바니아', '알제리', '앙골라', '앤티가 바부다',
                 '에리트레아', '에스토니아', '에콰도르', '에티오피아', '엘살바도르', '영국', '예멘', '오만',
                 '오스트레일리아', '오스트리아', '온두라스', '요르단', '우간다', '우루과이', '우즈베키스탄',
                 '우크라이나', '이라크', '이란', '이스라엘', '이집트', '이탈리아', '인도네시아', '일본',
                 '자메이카', '잠비아', '적도 기니', '조선민주주의인민공화국', '조지아', '중앙아프리카 공화국',
                 '중화인민공화국', '지부티', '짐바브웨', '차드', '체코', '칠레', '카메룬', '카보베르데',
                 '카자흐스탄', '카타르', '캄보디아', '캐나다', '케냐', '코모로', '코스타리카', '코트디부아르',
                 '콜롬비아', '콩고 공화국', '콩고 민주 공화국', '쿠바', '쿠웨이트', '크로아티아',
                 '키르기스스탄', '키리바시', '키프로스', '타이', '타지키스탄', '탄자니아', '터키',
                 '토고', '통가', '투르크메니스탄', '투발루', '튀니지', '트리니다드 토바고', '파나마',
                 '파라과이', '파키스탄', '파푸아 뉴기니', '팔라우', '페루', '포르투갈', '폴란드', '프랑스',
                 '피지', '핀란드', '필리핀', '헝가리',
                 )
    building_dongs = (
        '가',
        '나',
        '다',
        '라',
        '마',
        '바',
        '##',
        '###',
    )
    land_numbers = (
        '###',
        '###-#',
        '###-##',
    )
    road_numbers = (
        '#',
        '##',
        '###',
    )

    town_formats = (
        '{{first_name}}{{last_name}}{{town_suffix}}',
        '{{first_name}}{{last_name}}{{last_name}}{{town_suffix}}',
    )
    building_name_formats = (
        '{{first_name}}{{last_name}}{{building_suffix}}',
        '{{first_name}}{{last_name}}{{last_name}}{{building_suffix}}',
    )
    address_detail_formats = (
        '{{building_name}}',
        '{{building_name}} ###호',
        '{{building_name}} {{building_dong}}동 ###호',
    )
    road_formats = (
        '{{road_name}}{{road_suffix}}',
        '{{road_name}}{{road_number}}{{road_suffix}}',
    )
    road_address_formats = (
        '{{metropolitan_city}} {{borough}} {{road}}',
        '{{province}} {{city}} {{road}}',
        '{{metropolitan_city}} {{borough}} {{road}} ({{town}})',
        '{{province}} {{city}} {{road}} ({{town}})',
    )
    land_address_formats = (
        '{{metropolitan_city}} {{borough}} {{town}} {{land_number}}',
        '{{province}} {{city}} {{town}} {{land_number}}',
    )

    # Keep backward compatibility
    city_suffixes = ('시',)
    street_suffixes = road_suffixes
    street_name_formats = ('{{road_name}}',)
    street_address_formats = road_address_formats
    address_formats = road_address_formats

    def land_number(self):
        """
        :example 507
        """
        return self.bothify(self.random_element(self.land_numbers))

    def land_address(self):
        """
        :example 세종특별자치시 어진동 507
        """
        pattern = self.random_element(self.land_address_formats)
        return self.generator.parse(pattern)

    def road_number(self):
        """
        :example 24
        """
        return self.bothify(self.random_element(self.road_numbers))

    def road_address(self):
        """
        :example 세종특별자치시 도움5로 19 (어진동)
        """
        pattern = self.random_element(self.road_address_formats)
        return self.generator.parse(pattern)

    def address_detail(self):
        """
        :example 가나아파트 가동 102호
        """
        pattern = self.bothify(self.random_element(
            self.address_detail_formats))
        return self.generator.parse(pattern)

    def road(self):
        """
        :example 도움5로
        """
        pattern = self.random_element(self.road_formats)
        return self.generator.parse(pattern)

    def road_name(self):
        """
        :example 압구정
        """
        return self.random_element(self.road_names)

    def road_suffix(self):
        """
        :example 길
        """
        return self.random_element(self.road_suffixes)

    def metropolitan_city(self):
        """
        :example 서울특별시
        """
        return self.random_element(self.metropolitan_cities)

    def province(self):
        """
        :example 경기도
        """
        return self.random_element(self.provinces)

    def city(self):
        """
        :example 고양시
        """
        pattern = self.random_element(self.cities)
        return self.generator.parse(pattern)

    def borough(self):
        """
        :example 중구
        """
        return self.random_element(self.boroughs)

    def town(self):
        """
        :example 가나동
        """
        pattern = self.random_element(self.town_formats)
        return self.generator.parse(pattern)

    def town_suffix(self):
        """
        :example 동
        """
        return self.random_element(self.town_suffixes)

    def building_name(self):
        """
        :example 김구아파트
        """
        pattern = self.random_element(self.building_name_formats)
        return self.generator.parse(pattern)

    def building_suffix(self):
        """
        :example 아파트
        """
        return self.random_element(self.building_suffixes)

    def building_dong(self):
        """
        :example 가
        """
        return self.bothify(self.random_element(self.building_dongs))

    def old_postal_code(self):
        """
        :example 123-456
        """
        return self.bothify(self.random_element(self.postcode_formats))

    def postcode(self):
        """
        :example 12345
        """
        return self.bothify(self.random_element(self.new_postal_code_formats))

    def postal_code(self):
        """
        :example 12345
        """
        return self.postcode()
