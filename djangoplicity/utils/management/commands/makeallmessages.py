import os

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Run makemessages for all configured languages'

    def handle(self, *args, **options):
        for path in (settings.PRJBASE, settings.DJANGOPLICITY_ROOT):
            print path
            os.chdir(path)
            call_command('makemessagesnofuzzy')
