# coding: utf-8
from __future__ import unicode_literals

import pytest

from i18naddress import (
    get_field_order, get_validation_rules, load_validation_data)


def test_invalid_country_code():
    with pytest.raises(ValueError):
        load_validation_data('XX')
    with pytest.raises(ValueError):
        load_validation_data('../../../etc/passwd')


def test_dictionary_access():
    data = load_validation_data('US')
    state = data['US/NV']
    assert state['name'] == 'Nevada'


def test_validation_rules_canada():
    validation_data = get_validation_rules({'country_code': 'CA'})
    assert validation_data.country_code == 'CA'
    assert validation_data.country_area_choices == [
        ('AB', 'Alberta'),
        ('BC', 'British Columbia'),
        ('BC', 'Colombie-Britannique'),
        ('MB', 'Manitoba'),
        ('NB', 'New Brunswick'),
        ('NB', 'Nouveau-Brunswick'),
        ('NL', 'Newfoundland and Labrador'),
        ('NL', 'Terre-Neuve-et-Labrador'),
        ('NT', 'Northwest Territories'),
        ('NT', 'Territoires du Nord-Ouest'),
        ('NS', 'Nouvelle-Écosse'),
        ('NS', 'Nova Scotia'),
        ('NU', 'Nunavut'),
        ('ON', 'Ontario'),
        ('PE', 'Prince Edward Island'),
        ('PE', 'Île-du-Prince-Édouard'),
        ('QC', 'Quebec'),
        ('QC', 'Québec'),
        ('SK', 'Saskatchewan'),
        ('YT', 'Yukon')]


def test_validation_india():
    validation_data = get_validation_rules({'country_code': 'IN'})
    assert validation_data.country_area_choices == [
        ('Andaman and Nicobar Islands', 'Andaman & Nicobar'),
        ('Andhra Pradesh', 'Andhra Pradesh'),
        ('Andhra Pradesh', 'आंध्र प्रदेश'),
        ('Arunachal Pradesh', 'Arunachal Pradesh'),
        ('Arunachal Pradesh', 'अरुणाचल प्रदेश'),
        ('Assam', 'Assam'),
        ('Assam', 'असम'),
        ('Bihar', 'Bihar'),
        ('Bihar', 'बिहार'),
        ('Chandigarh', 'Chandigarh'),
        ('Chandigarh', 'चंडीगढ़'),
        ('Chhattisgarh', 'Chhattisgarh'),
        ('Chhattisgarh', 'छत्तीसगढ़'),
        ('Dadra and Nagar Haveli', 'Dadra & Nagar Haveli'),
        ('Daman and Diu', 'Daman & Diu'),
        ('Delhi', 'Delhi'),
        ('Delhi', 'दिल्ली'),
        ('Goa', 'Goa'),
        ('Goa', 'गोआ'),
        ('Gujarat', 'Gujarat'),
        ('Gujarat', 'गुजरात'),
        ('Haryana', 'Haryana'),
        ('Haryana', 'हरियाणा'),
        ('Himachal Pradesh', 'Himachal Pradesh'),
        ('Himachal Pradesh', 'हिमाचल प्रदेश'),
        ('Jammu and Kashmir', 'Jammu & Kashmir'),
        ('Jharkhand', 'Jharkhand'),
        ('Jharkhand', 'झारखण्ड'),
        ('Karnataka', 'Karnataka'),
        ('Karnataka', 'कर्नाटक'),
        ('Kerala', 'Kerala'),
        ('Kerala', 'केरल'),
        ('Lakshadweep', 'Lakshadweep'),
        ('Lakshadweep', 'लक्षद्वीप'),
        ('Madhya Pradesh', 'Madhya Pradesh'),
        ('Madhya Pradesh', 'मध्य प्रदेश'),
        ('Maharashtra', 'Maharashtra'),
        ('Maharashtra', 'महाराष्ट्र'),
        ('Manipur', 'Manipur'),
        ('Manipur', 'मणिपुर'),
        ('Meghalaya', 'Meghalaya'),
        ('Meghalaya', 'मेघालय'),
        ('Mizoram', 'Mizoram'),
        ('Mizoram', 'मिजोरम'),
        ('Nagaland', 'Nagaland'),
        ('Nagaland', 'नागालैंड'),
        ('Odisha', 'Odisha'),
        ('Odisha', 'ओड़िशा'),
        ('Puducherry', 'Puducherry'),
        ('Puducherry', 'पांडिचेरी'),
        ('Punjab', 'Punjab'),
        ('Punjab', 'पंजाब'),
        ('Rajasthan', 'Rajasthan'),
        ('Rajasthan', 'राजस्थान'),
        ('Sikkim', 'Sikkim'),
        ('Sikkim', 'सिक्किम'),
        ('Tamil Nadu', 'Tamil Nadu'),
        ('Tamil Nadu', 'तमिल नाडु'),
        ('Telangana', 'Telangana'),
        ('Telangana', 'तेलंगाना'),
        ('Tripura', 'Tripura'),
        ('Tripura', 'त्रिपुरा'),
        ('Uttar Pradesh', 'Uttar Pradesh'),
        ('Uttar Pradesh', 'उत्तर प्रदेश'),
        ('Uttarakhand', 'Uttarakhand'),
        ('Uttarakhand', 'उत्तराखण्ड'),
        ('West Bengal', 'West Bengal'),
        ('West Bengal', 'पश्चिम बंगाल'),
        ('Andaman & Nicobar', 'अंडमान और निकोबार द्वीपसमूह'),
        ('Jammu & Kashmir', 'जम्मू और कश्मीर'),
        ('Daman & Diu', 'दमन और दीव'),
        ('Dadra & Nagar Haveli', 'दादरा और नगर हवेली')]

def test_validation_rules_switzerland():
    validation_data = get_validation_rules({'country_code': 'CH'})
    assert validation_data.allowed_fields == {
        'company_name', 'city', 'postal_code', 'street_address', 'name'}
    assert validation_data.required_fields == {
        'city', 'postal_code', 'street_address'}


def test_field_order_poland():
    field_order = get_field_order({'country_code': 'PL'})
    assert field_order == [
        ['name'],
        ['company_name'],
        ['street_address'],
        ['postal_code', 'city']]


def test_field_order_china():
    field_order = get_field_order({'country_code': 'CN'})
    assert field_order == [
        ['postal_code'],
        ['country_area', 'city', 'city_area'],
        ['street_address'],
        ['company_name'],
        ['name']]


@pytest.mark.parametrize('country, levels', [
    ('CN', ['province', 'city', 'district']),
    ('JP', ['prefecture', 'city', 'suburb']),
    ('KR', ['do_si', 'city', 'district'])])
def test_locality_types(country, levels):
    validation_data = get_validation_rules({'country_code': country})
    assert validation_data.country_area_type == levels[0]
    assert validation_data.city_type == levels[1]
    assert validation_data.city_area_type == levels[2]
