from typing import TYPE_CHECKING, Dict, Iterable, List, Union

from django.db import transaction
from ..models import Follow


if TYPE_CHECKING:
    # flake8: noqa
    from datetime import date, datetime
    from django.db.models.query import QuerySet
