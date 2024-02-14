#!/usr/bin/env python3

# DO NOT FORK SALEOR TO EXTEND IT
# Learn more https://docs.saleor.io/docs/3.x/developer/extending/overview#why-not-to-fork

import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
