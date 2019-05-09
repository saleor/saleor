from django.core.management.base import BaseCommand

import silk.models


class Command(BaseCommand):
    help = "Clears silk's log of requests."

    @staticmethod
    def delete_model(model):
        while True:
            items_to_delete = list(
                model.objects.values_list('pk', flat=True).all()[:1000])
            if not items_to_delete:
                break
            model.objects.filter(pk__in=items_to_delete).delete()

    def handle(self, *args, **options):
        # Django takes a long time to traverse foreign key relations,
        # so delete in the order that makes it easy.
        Command.delete_model(silk.models.Profile)
        Command.delete_model(silk.models.SQLQuery)
        Command.delete_model(silk.models.Response)
        Command.delete_model(silk.models.Request)
