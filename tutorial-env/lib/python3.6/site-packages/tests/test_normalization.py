# coding: utf-8
from __future__ import unicode_literals

import pytest

from i18naddress import (
    InvalidAddress, format_address, latinize_address, normalize_address)


@pytest.mark.parametrize('address, errors', [
    ({},
     {'country_code': 'required', 'city': 'required',
      'street_address': 'required'}),
    ({'country_code': 'AR'},
     {'city': 'required', 'street_address': 'required'}),
    ({'country_code': 'CN', 'country_area': '北京市', 'postal_code': '100084',
      'city': 'Invalid', 'street_address': '...'},
     {'city': 'invalid'}),
    ({'country_code': 'CN', 'country_area': '云南省', 'postal_code': '677400',
      'city': '临沧市', 'city_area': 'Invalid', 'street_address': '...'},
     {'city_area': 'invalid'}),
    ({'country_code': 'DE', 'city': 'Berlin', 'postal_code': '77-777',
      'street_address': '...'},
     {'postal_code': 'invalid'}),
    ({'country_code': 'PL', 'city': 'Wrocław', 'postal_code': '77777',
      'street_address': '...'},
     {'postal_code': 'invalid'}),
    ({'country_code': 'KR'},
     {'country_area': 'required', 'postal_code': 'required',
      'city': 'required', 'street_address': 'required'}),
    ({'country_code': 'US', 'country_area': 'Nevada',
      'postal_code': '90210', 'city': 'Las Vegas', 'street_address': '...'},
     {'postal_code': 'invalid'}),
    ({'country_code': 'XX'},
     {'country_code': 'invalid'}),
    ({'country_code': 'ZZ'},
     {'country_code': 'invalid'})])
def test_validate_areas_errors(address, errors):
    with pytest.raises(InvalidAddress) as excinfo:
        normalize_address(address)
    assert excinfo.value.errors == errors


@pytest.mark.parametrize('address', [
    {'country_code': 'AE', 'country_area': 'Dubai', 'city': 'Dubai',
     'street_address': 'P.O Box 1234'},
    {'country_code': 'CA', 'country_area': 'QC', 'city': 'Montreal',
     'postal_code': 'H3Z 2Y7', 'street_address': '10-123 1/2 MAIN STREET NW'},
    {'country_code': 'CH', 'city': 'Zürich', 'postal_code': '8022',
     'street_address': 'Kappelergasse 1'},
    {'country_code': 'CN', 'country_area': '北京市', 'postal_code': '100084',
     'city': '海淀区', 'street_address': '中关村东路1号'},
    {'country_code': 'CN', 'country_area': '云南省', 'postal_code': '677400',
     'city': '临沧市', 'city_area': '凤庆县', 'street_address': '中关村东路1号'},
    {'country_code': 'CN', 'country_area': 'Beijing Shi',
     'postal_code': '100084', 'city': 'Haidian Qu',
     'street_address': '#1 Zhongguancun East Road'},
    {'country_code': 'JP', 'country_area': '東京都', 'postal_code': '150-8512',
     'city': '渋谷区', 'street_address': '桜丘町26-1'},
    {'country_code': 'JP', 'country_area': 'Tokyo', 'postal_code': '150-8512',
     'city': 'Shibuya-ku', 'street_address': '26-1 Sakuragaoka-cho'},
    {'country_code': 'KR', 'country_area': '서울', 'postal_code': '06136',
     'city': '강남구', 'street_address': '역삼동 737번지 강남파이낸스센터'},
    {'country_code': 'KR', 'country_area': '서울특별시', 'postal_code': '06136',
     'city': '강남구', 'street_address': '역삼동 737번지 강남파이낸스센터'},
    {'country_code': 'KR', 'country_area': 'Seoul', 'postal_code': '06136',
     'city': 'Gangnam-gu', 'street_address': '역삼동 737번지 강남파이낸스센터'},
    {'country_code': 'PL', 'city': 'Warszawa', 'postal_code': '00-374',
     'street_address': 'Aleje Jerozolimskie 2'},
    {'country_code': 'US', 'country_area': 'California',
     'postal_code': '94037', 'city': 'Mountain View',
     'street_address': '1600 Charleston Rd.'}])
def test_validate_known_addresses(address):
    assert normalize_address(address)


def test_localization_handling():
    address = normalize_address({
        'country_code': 'us',
        'country_area': 'California',
        'postal_code': '94037',
        'city': 'Mountain View',
        'street_address': '1600 Charleston Rd.'})
    assert address['country_code'] == 'US'
    assert address['country_area'] == 'CA'
    address = normalize_address({
        'country_code': 'us',
        'country_area': 'CALIFORNIA',
        'postal_code': '94037',
        'city': 'Mountain View',
        'street_address': '1600 Charleston Rd.'})
    assert address['country_area'] == 'CA'
    address = normalize_address({
        'country_code': 'CN',
        'country_area': 'Beijing Shi',
        'postal_code': '100084',
        'city': 'Haidian Qu',
        'street_address': '#1 Zhongguancun East Road'})
    assert address['country_area'] == '北京市'
    assert address['city'] == '海淀区'
    address = normalize_address({
        'country_code': 'AE',
        'country_area': 'Dubai',
        'postal_code': '123456',
        'sorting_code': '654321',
        'street_address': 'P.O Box 1234'})
    assert address['country_area'] == 'إمارة دبيّ'
    assert address['city'] == ''
    assert address['postal_code'] == ''
    assert address['sorting_code'] == ''


def test_address_formatting():
    address = {
        'country_code': 'CN',
        'country_area': '云南省',
        'postal_code': '677400',
        'city': '临沧市',
        'city_area': '凤庆县',
        'street_address': '中关村东路1号'}
    result = format_address(address, latin=False)
    assert result == (
        '677400\n'
        '云南省临沧市凤庆县\n'
        '中关村东路1号\n'
        'CHINA')


def test_capitalization():
    address = normalize_address({
        'country_code': 'GB',
        'postal_code': 'sw1a 0aa',
        'city': 'London',
        'street_address': 'Westminster'})
    assert address['city'] == 'LONDON'
    assert address['postal_code'] == 'SW1A 0AA'


def test_address_latinization():
    address = {}
    address = latinize_address(address, normalized=True)
    assert address == {}
    address = {
        'country_code': 'US',
        'country_area': 'CA',
        'postal_code': '94037',
        'city': 'Mountain View',
        'street_address': '1600 Charleston Rd.'}
    address = latinize_address(address)
    assert address['country_area'] == 'California'
    address = {
        'country_code': 'CN',
        'country_area': '云南省',
        'postal_code': '677400',
        'city': '临沧市',
        'city_area': '凤庆县',
        'street_address': '中关村东路1号'}
    address = latinize_address(address)
    assert address == {
        'country_code': 'CN',
        'country_area': 'Yunnan Sheng',
        'postal_code': '677400',
        'city': 'Lincang Shi',
        'city_area': 'Fengqing Xian',
        'street_address': '中关村东路1号',
        'sorting_code': ''}
    address = {
        'name': 'Zhang San',
        'company_name': 'Beijing Kid Toy Company',
        'country_code': 'CN',
        'country_area': '北京市',
        'city': '海淀区',
        'postal_code': '100084',
        'sorting_code': '',
        'street_address': '#1 Zhongguancun East Road'}
    address = latinize_address(address)
    result = format_address(address, latin=True)
    assert result == (
        'Zhang San\n'
        'Beijing Kid Toy Company\n'
        '#1 Zhongguancun East Road\n'
        'Haidian Qu\n'
        'BEIJING SHI, 100084\n'
        'CHINA')
