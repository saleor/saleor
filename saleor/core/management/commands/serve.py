from django.contrib.staticfiles.management.commands.runserver import Command \
    as RunServer
from django.core.servers import basehttp


original_log_message = basehttp.WSGIRequestHandler.log_message


def log_local_message(self, format, *args):
    format = "[%s] " % self.address_string() + format
    return original_log_message(self, format, *args)


basehttp.WSGIRequestHandler.log_message = log_local_message


class Command(RunServer):
    def handle(self, *args, **options):
        return super(Command, self).handle(*args, **options)
