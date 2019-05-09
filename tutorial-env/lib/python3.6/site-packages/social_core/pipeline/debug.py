from pprint import pprint


def debug(response, details, *args, **kwargs):
    print('=' * 80)
    pprint(response)
    print('=' * 80)
    pprint(details)
    print('=' * 80)
    pprint(args)
    print('=' * 80)
    pprint(kwargs)
    print('=' * 80)
