# coding: utf8
"""
    cssselect2.tests
    ----------------

    Test suite for cssselect2.

    :copyright: (c) 2012 by Simon Sapin, 2017 by Guillaume Ayoub.
    :license: BSD, see LICENSE for more details.

"""

import json
import os.path
import xml.etree.ElementTree as etree

import pytest

from cssselect2 import ElementWrapper, SelectorError, compile_selector_list


def resource(filename):
    return os.path.join(os.path.dirname(__file__), filename)


def load_json(filename):
    return json.load(open(resource(filename)))


def get_test_document():
    document = etree.parse(resource('content.xhtml'))
    parent = next(e for e in document.getiterator() if e.get('id') == 'root')

    # Setup namespace tests
    for id in ('any-namespace', 'no-namespace'):
        div = etree.SubElement(parent, '{http://www.w3.org/1999/xhtml}div')
        div.set('id', id)
        etree.SubElement(div, '{http://www.w3.org/1999/xhtml}div') \
            .set('id', id + '-div1')
        etree.SubElement(div, '{http://www.w3.org/1999/xhtml}div') \
            .set('id', id + '-div2')
        etree.SubElement(div, 'div').set('id', id + '-div3')
        etree.SubElement(div, '{http://www.example.org/ns}div') \
            .set('id', id + '-div4')

    return document


TEST_DOCUMENT = get_test_document()


@pytest.mark.parametrize('test', load_json('invalid_selectors.json'))
def test_invalid_selectors(test):
    if test.get('xfail'):
        pytest.xfail()
    try:
        compile_selector_list(test['selector'])
    except SelectorError:
        pass
    else:
        raise AssertionError('Should be invalid: %(selector)r %(name)s' % test)


@pytest.mark.parametrize('test', load_json('valid_selectors.json'))
def test_valid_selectors(test):
    if test.get('xfail'):
        pytest.xfail()
    exclude = test.get('exclude', ())
    if 'document' in exclude or 'xhtml' in exclude:
        return
    root = ElementWrapper.from_xml_root(TEST_DOCUMENT)
    result = [e.id for e in root.query_all(test['selector'])]
    if result != test['expect']:
        print(test['selector'])
        print(result)
        print('!=')
        print(test['expect'])
        raise AssertionError(test['name'])


def test_lang():
    doc = etree.fromstring('''
        <html xmlns="http://www.w3.org/1999/xhtml"></html>
    ''')
    assert not ElementWrapper.from_xml_root(doc).matches(':lang(fr)')

    doc = etree.fromstring('''
        <html xmlns="http://www.w3.org/1999/xhtml">
            <meta http-equiv="Content-Language" content=" fr \t"/>
        </html>
    ''')
    root = ElementWrapper.from_xml_root(doc, content_language='en')
    assert root.matches(':lang(fr)')

    doc = etree.fromstring('''
        <html>
            <meta http-equiv="Content-Language" content=" fr \t"/>
        </html>
    ''')
    root = ElementWrapper.from_xml_root(doc, content_language='en')
    assert root.matches(':lang(en)')

    doc = etree.fromstring('<html></html>')
    root = ElementWrapper.from_xml_root(doc, content_language='en')
    assert root.matches(':lang(en)')

    root = ElementWrapper.from_xml_root(doc, content_language='en, es')
    assert not root.matches(':lang(en)')

    root = ElementWrapper.from_xml_root(doc)
    assert not root.matches(':lang(en)')

    doc = etree.fromstring('<html lang="eN"></html>')
    root = ElementWrapper.from_html_root(doc)
    assert root.matches(':lang(en)')

    doc = etree.fromstring('<html lang="eN"></html>')
    root = ElementWrapper.from_xml_root(doc)
    assert not root.matches(':lang(en)')


def test_select():
    root = etree.fromstring(HTML_IDS)

    def select_ids(selector, html_only):
        xml_ids = [element.etree_element.get('id', 'nil') for element in
                   ElementWrapper.from_xml_root(root).query_all(selector)]
        html_ids = [element.etree_element.get('id', 'nil') for element in
                    ElementWrapper.from_html_root(root).query_all(selector)]
        if html_only:
            assert xml_ids == []
        else:
            assert xml_ids == html_ids
        return html_ids

    def pcss(main, *selectors, **kwargs):
        html_only = kwargs.pop('html_only', False)
        result = select_ids(main, html_only)
        for selector in selectors:
            assert select_ids(selector, html_only) == result
        return result

    all_ids = pcss('*')
    assert all_ids[:6] == [
        'html', 'nil', 'link-href', 'link-nohref', 'nil', 'outer-div']
    assert all_ids[-1:] == ['foobar-span']
    assert pcss('div') == ['outer-div', 'li-div', 'foobar-div']
    assert pcss('DIV', html_only=True) == [
        'outer-div', 'li-div', 'foobar-div']  # case-insensitive in HTML
    assert pcss('div div') == ['li-div']
    assert pcss('div, div div') == ['outer-div', 'li-div', 'foobar-div']
    assert pcss('div , div div') == ['outer-div', 'li-div', 'foobar-div']
    assert pcss('a[name]') == ['name-anchor']
    assert pcss('a[NAme]', html_only=True) == [
        'name-anchor']  # case-insensitive in HTML:
    assert pcss('a[rel]') == ['tag-anchor', 'nofollow-anchor']
    assert pcss('a[rel="tag"]') == ['tag-anchor']
    assert pcss('a[href*="localhost"]') == ['tag-anchor']
    assert pcss('a[href*=""]') == []
    assert pcss('a[href^="http"]') == ['tag-anchor', 'nofollow-anchor']
    assert pcss('a[href^="http:"]') == ['tag-anchor']
    assert pcss('a[href^=""]') == []
    assert pcss('a[href$="org"]') == ['nofollow-anchor']
    assert pcss('a[href$=""]') == []
    assert pcss('div[foobar~="bc"]', 'div[foobar~="cde"]') == [
        'foobar-div']
    assert pcss('[foobar~="ab bc"]',
                '[foobar~=""]', '[foobar~=" \t"]') == []
    assert pcss('div[foobar~="cd"]') == []
    assert pcss('*[lang|="En"]', '[lang|="En-us"]') == ['second-li']
    # Attribute values are case sensitive
    assert pcss('*[lang|="en"]', '[lang|="en-US"]') == []
    assert pcss('*[lang|="e"]') == []
    # ... :lang() is not.
    assert pcss(
        ':lang(EN)', '*:lang(en-US)'
        ':lang(En)'
    ) == ['second-li', 'li-div']
    assert pcss(':lang(e)'  # , html_only=True
                ) == []
    assert pcss('li:nth-child(3)') == ['third-li']
    assert pcss('li:nth-child(10)') == []
    assert pcss('li:nth-child(2n)', 'li:nth-child(even)',
                'li:nth-child(2n+0)') == [
        'second-li', 'fourth-li', 'sixth-li']
    assert pcss('li:nth-child(+2n+1)', 'li:nth-child(odd)') == [
        'first-li', 'third-li', 'fifth-li', 'seventh-li']
    assert pcss('li:nth-child(2n+4)') == ['fourth-li', 'sixth-li']
    assert pcss('li:nth-child(3n+1)') == [
        'first-li', 'fourth-li', 'seventh-li']
    assert pcss('li:nth-last-child(1)') == ['seventh-li']
    assert pcss('li:nth-last-child(0)') == []
    assert pcss('li:nth-last-child(2n+2)', 'li:nth-last-child(even)') == [
        'second-li', 'fourth-li', 'sixth-li']
    assert pcss('li:nth-last-child(2n+4)') == ['second-li', 'fourth-li']
    assert pcss('ol:first-of-type') == ['first-ol']
    assert pcss('ol:nth-child(1)') == []
    assert pcss('ol:nth-of-type(2)') == ['second-ol']
    assert pcss('ol:nth-last-of-type(2)') == ['first-ol']
    assert pcss('span:only-child') == ['foobar-span']
    assert pcss('div:only-child') == ['li-div']
    assert pcss('div *:only-child') == ['li-div', 'foobar-span']
    assert pcss('p *:only-of-type') == ['p-em', 'fieldset']
    assert pcss('p:only-of-type') == ['paragraph']
    assert pcss('a:empty', 'a:EMpty') == ['name-anchor']
    assert pcss('li:empty') == [
        'third-li', 'fourth-li', 'fifth-li', 'sixth-li']
    assert pcss(':root', 'html:root') == ['html']
    assert pcss('li:root', '* :root') == []
    assert pcss('.a', '.b', '*.a', 'ol.a') == ['first-ol']
    assert pcss('.c', '*.c') == ['first-ol', 'third-li', 'fourth-li']
    assert pcss('ol *.c', 'ol li.c', 'li ~ li.c', 'ol > li.c') == [
        'third-li', 'fourth-li']
    assert pcss('#first-li', 'li#first-li', '*#first-li') == ['first-li']
    assert pcss('li div', 'li > div', 'div div') == ['li-div']
    assert pcss('div > div') == []
    assert pcss('div>.c', 'div > .c') == ['first-ol']
    assert pcss('div + div') == ['foobar-div']
    assert pcss('a ~ a') == ['tag-anchor', 'nofollow-anchor']
    assert pcss('a[rel="tag"] ~ a') == ['nofollow-anchor']
    assert pcss('ol#first-ol li:last-child') == ['seventh-li']
    assert pcss('ol#first-ol *:last-child') == ['li-div', 'seventh-li']
    assert pcss('#outer-div:first-child') == ['outer-div']
    assert pcss('#outer-div :first-child') == [
        'name-anchor', 'first-li', 'li-div', 'p-b',
        'checkbox-fieldset-disabled', 'area-href']
    assert pcss('a[href]') == ['tag-anchor', 'nofollow-anchor']
    assert pcss(':not(*)') == []
    assert pcss('a:not([href])') == ['name-anchor']
    assert pcss('ol :Not([class])') == [
        'first-li', 'second-li', 'li-div',
        'fifth-li', 'sixth-li', 'seventh-li']
    # Invalid characters in XPath element names, should not crash
    assert pcss(r'di\a0 v', r'div\[') == []
    assert pcss(r'[h\a0 ref]', r'[h\]ref]') == []

    assert pcss(':link') == [
        'link-href', 'tag-anchor', 'nofollow-anchor', 'area-href']
    assert pcss('HTML :link', html_only=True) == [
        'link-href', 'tag-anchor', 'nofollow-anchor', 'area-href']
    assert pcss(':visited') == []
    assert pcss(':enabled') == [
        'link-href', 'tag-anchor', 'nofollow-anchor',
        'checkbox-unchecked', 'text-checked', 'input-hidden',
        'checkbox-checked', 'area-href']
    assert pcss(':disabled') == [
        'checkbox-disabled', 'input-hidden-disabled',
        'checkbox-disabled-checked', 'fieldset',
        'checkbox-fieldset-disabled',
        'hidden-fieldset-disabled']
    assert pcss(':checked') == [
        'checkbox-checked', 'checkbox-disabled-checked']


def test_select_shakespeare():
    document = etree.fromstring(HTML_SHAKESPEARE)
    body = document.find('.//{http://www.w3.org/1999/xhtml}body')
    body = ElementWrapper.from_xml_root(body)

    def count(selector):
        return sum(1 for _ in body.query_all(selector))

    # Data borrowed from http://mootools.net/slickspeed/

    # # Changed from original; probably because I'm only
    # # searching the body.
    # assert count('*') == 252
    assert count('*') == 246
    # assert count('div:contains(CELIA)') == 26
    assert count('div:only-child') == 22  # ?
    assert count('div:nth-child(even)') == 106
    assert count('div:nth-child(2n)') == 106
    assert count('div:nth-child(odd)') == 137
    assert count('div:nth-child(2n+1)') == 137
    assert count('div:nth-child(n)') == 243
    assert count('div:last-child') == 53
    assert count('div:first-child') == 51
    assert count('div > div') == 242
    assert count('div + div') == 190
    assert count('div ~ div') == 190
    assert count('body') == 1
    assert count('body div') == 243
    assert count('div') == 243
    assert count('div div') == 242
    assert count('div div div') == 241
    assert count('div, div, div') == 243
    assert count('div, a, span') == 243
    assert count('.dialog') == 51
    assert count('div.dialog') == 51
    assert count('div .dialog') == 51
    assert count('div.character, div.dialog') == 99
    assert count('div.direction.dialog') == 0
    assert count('div.dialog.direction') == 0
    assert count('div.dialog.scene') == 1
    assert count('div.scene.scene') == 1
    assert count('div.scene .scene') == 0
    assert count('div.direction .dialog ') == 0
    assert count('div .dialog .direction') == 4
    assert count('div.dialog .dialog .direction') == 4
    assert count('#speech5') == 1
    assert count('div#speech5') == 1
    assert count('div #speech5') == 1
    assert count('div.scene div.dialog') == 49
    assert count('div#scene1 div.dialog div') == 142
    assert count('#scene1 #speech1') == 1
    assert count('div[class]') == 103
    assert count('div[class=dialog]') == 50
    assert count('div[class^=dia]') == 51
    assert count('div[class$=log]') == 50
    assert count('div[class*=sce]') == 1
    assert count('div[class|=dialog]') == 50  # ? Seems right
    # assert count('div[class!=madeup]') == 243  # ? Seems right
    assert count('div[class~=dialog]') == 51  # ? Seems right


HTML_IDS = open(resource('ids.html')).read()
HTML_SHAKESPEARE = open(resource('shakespeare.html')).read()
