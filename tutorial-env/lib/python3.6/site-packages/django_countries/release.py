"""
This file provides zest.releaser entrypoints using when releasing new
django-countries versions.
"""
import os

from txclib.commands import cmd_pull
from txclib.utils import find_dot_tx
from txclib.log import logger
from zest.releaser.utils import ask, execute_command
from django.core.management import call_command
import django_countries


def translations(data):
    if data["name"] != "django-countries":
        return

    if not ask("Pull translations from transifex and compile", default=True):
        return

    _handlers = logger.handlers
    logger.handlers = []
    try:
        cmd_pull(argv=["-a", "--minimum-perc=60"], path_to_tx=find_dot_tx())
    finally:
        logger.handlers = _handlers

    _cwd = os.getcwd()
    os.chdir(os.path.dirname(django_countries.__file__))
    try:
        call_command("compilemessages")
        execute_command(["git", "add", "locale"])
    finally:
        os.chdir(_cwd)
