import os
from subprocess import call
from importlib import import_module

from django import db
from django.core.management.base import BaseCommand, CommandError


CHOICES = ('dev', 'int', 'prod')
DUMP_FILE = '/tmp/db.dump'

VALID_ENGINES = (
    'django.db.backends.postgresql',
    'django.db.backends.postgresql_psycopg2',
)


def run(command):
    result = call(command, shell=True)
    if result != 0:
        raise CommandError('Command {} exited with {}'.format(command, result))


class Command(BaseCommand):
    help = 'Copy the DB from the source to the destination'

    def add_arguments(self, parser):
        parser.add_argument('src', choices=CHOICES, default='prod', nargs='?',
            help='Source DB (default: prod)')
        parser.add_argument('dst', choices=CHOICES, default='dev', nargs='?',
            help='Destination DB (default: dev)')

    def handle(self, *args, **options):
        src = options['src']
        dst = options['dst']

        if dst == 'prod':
            raise CommandError('Copying to production DB is not allowed')

        # Get the main package name from the environment
        package = os.environ['DJANGO_SETTINGS_MODULE'].split('.')[0]

        # Get the database settings from the src and dst
        src_dbs = import_module('{}.{}'.format(package, src)).DATABASES
        dst_dbs = import_module('{}.{}'.format(package, dst)).DATABASES

        src_db = src_dbs['default']
        dst_db = dst_dbs['default']

        if src_db['ENGINE'] not in VALID_ENGINES:
            raise CommandError('DB engine not implemented: {}'.format(
                src_db['ENGINE']))

        if dst_db['ENGINE'] not in VALID_ENGINES:
            raise CommandError('DB engine not implemented: {}'.format(
                dst_db['ENGINE']))

        # Dump the src DB
        self.stdout.write('Dumping {} from {}'.format(src_db['NAME'],
            src_db['HOST']))

        command = 'pg_dump --format=custom --host={host} --username={user} ' \
            '--no-owner {db_name} > {dump_file}'
        run(command.format(
            host=src_db['HOST'],
            user=src_db['USER'],
            db_name=src_db['NAME'],
            dump_file=DUMP_FILE,
        ))

        # Dropping dst DB
        self.stdout.write('Dropping {} on {}'.format(dst_db['NAME'],
            dst_db['HOST']))

        # We first need to close all active connections
        db.connections.close_all()

        command = 'dropdb --if-exists --host={host} --username={user} ' \
            '{db_name}'
        run(command.format(
            host=dst_db['HOST'],
            user=dst_db['USER'],
            db_name=dst_db['NAME'],
        ))

        # Creating dst DB
        self.stdout.write('Creating {} on {}'.format(dst_db['NAME'],
            dst_db['HOST']))

        command = 'createdb --owner={user} --host={host} --username={user} ' \
            '{db_name}'
        run(command.format(
            host=dst_db['HOST'],
            user=dst_db['USER'],
            db_name=dst_db['NAME'],
        ))

        # Restoring dst DB
        self.stdout.write('Restoring {} on {}'.format(dst_db['NAME'],
            dst_db['HOST']))

        command = 'pg_restore --host={host} --username={user} --no-owner ' \
            '--dbname={db_name} --schema=public {dump_file}'
        run(command.format(
            host=dst_db['HOST'],
            user=dst_db['USER'],
            db_name=dst_db['NAME'],
            dump_file=DUMP_FILE,
        ))

        # Delete dump file
        run('rm {}'.format(DUMP_FILE))
