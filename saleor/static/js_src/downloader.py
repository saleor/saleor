#!/usr/bin/env python3
import json
from multiprocessing.pool import ThreadPool
from multiprocessing import JoinableQueue, Queue

import requests

MAIN_URL = 'http://i18napis.appspot.com/address/data'


work_queue = JoinableQueue()
response_queue = Queue()


def fetch(url):
    print(url)
    data = requests.get(url).json()
    return data


def process(key):
    url = '%s/%s' % (MAIN_URL, key)
    data = fetch(url)
    for unwanted in [
            'id', 'isoid', 'key', 'posturl', 'sub_isoids', 'sub_mores',
            'sub_xrequires', 'sub_xzips', 'sub_zipexs']:
        if unwanted in data:
            del data[unwanted]
    lang = data.pop('lang', None)
    languages = data.pop('languages', None)
    if data:
        response_queue.put((key, data))
    if languages is not None:
        langs = languages.split('~')
        langs.remove(lang)
        for lang in langs:
            work_queue.put('%s--%s' % (key, lang))
    if 'sub_keys' in data:
        sub_keys = data['sub_keys'].split('~')
        for sub_key in sub_keys:
            work_queue.put('%s/%s' % (key, sub_key))


def worker():
    while True:
        try:
            key = work_queue.get()
        except EOFError:
            break
        process(key)
        work_queue.task_done()

countries = fetch(MAIN_URL)['countries'].split('~')
for country in countries:
    work_queue.put(country)
workers = ThreadPool(16, worker)
data = {}
work_queue.join()
workers.terminate()
while not response_queue.empty():
    key, value = response_queue.get()
    print(key)
    data[key] = value
with open('address.json', 'w', encoding='utf8') as output:
    json.dump(data, output, indent=2, ensure_ascii=False)
