from __future__ import unicode_literals

import io
import json
import logging
import os
from multiprocessing import JoinableQueue, Manager
from multiprocessing.pool import ThreadPool

import requests

from . import VALIDATION_DATA_DIR

MAIN_URL = 'https://chromium-i18n.appspot.com/ssl-address/data'
DATA_PATH = os.path.join(VALIDATION_DATA_DIR, '%s.json')

logger = logging.getLogger(__name__)
work_queue = JoinableQueue()
manager = Manager()


def fetch(url):  # pragma: no cover
    logger.debug(url)
    data = requests.get(url).json()
    return data


def get_countries():  # pragma: no cover
    return fetch(MAIN_URL)['countries'].split('~') + ['ZZ']


def process(key, language):
    full_key = '%s--%s' % (key, language) if language else key
    url = '%s/%s' % (MAIN_URL, full_key)
    data = fetch(url)
    lang = data.get('lang')
    languages = data.get('languages')
    if languages is not None:
        langs = languages.split('~')
        langs.remove(lang)
        for lang in langs:
            work_queue.put((key, lang))
    if 'sub_keys' in data:
        sub_keys = data['sub_keys'].split('~')
        for sub_key in sub_keys:
            work_queue.put(('%s/%s' % (key, sub_key), language))
    return full_key, data


def worker(data):  # pragma: no cover
    while True:
        try:
            key, lang = work_queue.get()
        except EOFError:
            break
        try:
            full_key, address_data = process(key, lang)
        except Exception:
            logger.exception('Can\'t download %s', key)
            work_queue.put((key, lang))
        else:
            data[full_key] = address_data
        work_queue.task_done()


def serialize(obj, path):
    with io.open(path, 'w', encoding='utf8') as output:
        data_str = json.dumps(dict(obj), ensure_ascii=False, sort_keys=True)
        output.write(data_str)
        return data_str


def download(country=None, processes=16):
    if not os.path.exists(VALIDATION_DATA_DIR):
        os.mkdir(VALIDATION_DATA_DIR)
    data = manager.dict()
    countries = get_countries()
    if country:
        country = country.upper()
        if country not in countries:
            raise ValueError(
                '%s is not supported country code' % country)
        countries = [country]
    for country in countries:
        work_queue.put((country, None))
    workers = ThreadPool(processes, worker, initargs=(data,))
    work_queue.join()
    workers.terminate()
    logger.debug('Queue finished')
    with io.open(DATA_PATH % 'all', 'w', encoding='utf8') as all_output:
        all_output.write(u'{')
        for country in countries:
            country_dict = {}
            for key, address_data in data.items():
                if key[:2] == country:
                    country_dict[key] = address_data
            logger.debug('Saving %s', country)
            country_json = serialize(
                country_dict, DATA_PATH % country.lower())
            all_output.write(country_json[1:-1])
            if country != countries[-1]:
                all_output.write(u',')
        all_output.write(u'}')
