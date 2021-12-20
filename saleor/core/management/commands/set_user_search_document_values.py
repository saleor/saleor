from typing import Any

from django.core.management import BaseCommand

from ....account.models import User
from ...search_tasks import set_user_search_document_values


class Command(BaseCommand):
    help = "Used to set search document values for users."

    def handle(self, *args: Any, **options: Any):
        total_count = User.objects.filter(search_document="").count()
        set_user_search_document_values.delay(total_count, 0)
