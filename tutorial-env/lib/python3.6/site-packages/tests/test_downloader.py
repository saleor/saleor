# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import os

from i18naddress.downloader import download, process
import pytest

try:
    from unittest import mock
except ImportError:
    import mock


@pytest.fixture(autouse=True)
def patch_i18n_country_data(monkeypatch, tmpdir):
    manager_dict = {'PL': 'datą', 'US': 'data'}
    all_countries = ['PL', 'US']
    data_dir = tmpdir.join('data')
    monkeypatch.setattr('i18naddress.downloader.ThreadPool', mock.MagicMock())
    monkeypatch.setattr('i18naddress.downloader.work_queue', mock.MagicMock())
    monkeypatch.setattr(
        'i18naddress.downloader.get_countries', lambda: all_countries)
    monkeypatch.setattr(
        'i18naddress.downloader.VALIDATION_DATA_DIR', str(data_dir))
    monkeypatch.setattr(
        'i18naddress.downloader.DATA_PATH',
        os.path.join(str(data_dir), '%s.json'))
    manager = mock.MagicMock()
    manager.dict.return_value = manager_dict
    monkeypatch.setattr('i18naddress.downloader.manager', manager)


@pytest.mark.parametrize('country, file_names, data', [
    (None, ('pl.json', 'us.json', 'all.json'), {
        'pl.json': {'PL': 'datą'},
        'us.json': {'US': 'data'},
        'all.json': {'PL': 'datą', 'US': 'data'}}),
    ('PL', ('pl.json', 'all.json'), {
        'pl.json': {'PL': 'datą'},
        'all.json': {'PL': 'datą'}})])
def test_downloader_country(tmpdir, country, file_names, data):
    data_dir = tmpdir.join('data')
    download(country)
    for file_name in file_names:
        assert data_dir.join(file_name).exists()
        assert json.load(
            data_dir.join(file_name), encoding='utf-8') == data[file_name]


def test_downloader_invalid_country():
    with pytest.raises(ValueError):
        download('XX')


@pytest.mark.parametrize('fetched_data, country, calls', [
    ({'lang': 'de', 'name': 'SWITZERLAND', 'languages': 'de~fr',
      'sub_keys': 'AG~AR', 'sub_names': 'Aargau~Appenzell Ausserrhoden'},
     'CH',
     [mock.call(('CH', 'fr')),
      mock.call(('CH/AG', None)),
      mock.call(('CH/AR', None))]),
    ({'lang': 'de', 'name': 'GERMANY'}, 'CH', ())])
def test_process(monkeypatch, fetched_data, country, calls):
    work_queue_put = mock.Mock(return_value=None)
    monkeypatch.setattr('i18naddress.downloader.work_queue.put', work_queue_put)
    monkeypatch.setattr('i18naddress.downloader.fetch', lambda url: fetched_data)
    key, data = process(country, None)
    work_queue_put.assert_has_calls(calls)
    assert key == 'CH'
    assert data == fetched_data


def test_downloader_with_existing_data_dir(tmpdir):
    data_dir = tmpdir.mkdir('data')
    download('PL')
    assert data_dir.join('pl.json').exists()
