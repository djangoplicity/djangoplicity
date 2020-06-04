from __future__ import unicode_literals

import os
from importlib import import_module

import django
from django.core.management.base import BaseCommand, CommandError

from .psql_copy import VALID_ENGINES, run


class Command(BaseCommand):
    help = 'Restore a PSQL dump file to the local dev database server'

    def add_arguments(self, parser):
        parser.add_argument('FILE')

    def handle(self, *args, **options):
        path = options['FILE']

        # Get the main package name from the environment
        package = os.environ['DJANGO_SETTINGS_MODULE'].split('.')[0]

        dbs = import_module('{}.dev'.format(package)).DATABASES
        db = dbs['default']

        if db['ENGINE'] not in VALID_ENGINES:
            raise CommandError('DB engine not implemented: {}'.format(
                db['ENGINE']))

        # Dropping DB
        self.stdout.write('Dropping {} on {}'.format(db['NAME'], db['HOST']))

        # We first need to close all active connections
        django.db.connections.close_all()

        command = 'dropdb --if-exists --host={host} --username={user} ' \
            '{db_name}'
        run(command.format(
            host=db['HOST'],
            user=db['USER'],
            db_name=db['NAME'],
        ))

        # Creating DB
        self.stdout.write('Creating {} on {}'.format(db['NAME'],
            db['HOST']))

        command = 'createdb --owner={user} --host={host} --username={user} ' \
            '{db_name}'
        run(command.format(
            host=db['HOST'],
            user=db['USER'],
            db_name=db['NAME'],
        ))

        self.stdout.write('Restoring {} to {}'.format(path, db['HOST']))

        command = 'pg_restore --host={host} --username={user} --no-owner ' \
            '--dbname={db_name} --schema=public {dump_file}'

        run(command.format(
            host=db['HOST'],
            user=db['USER'],
            db_name=db['NAME'],
            dump_file=path,
        ))
