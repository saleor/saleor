#!/usr/bin/env python

version = "n0t-3v3n-v3rs10ned.y3t"


def manage():
    import os
    import sys
    from django.core.management import execute_from_command_line

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
    execute_from_command_line(sys.argv)
