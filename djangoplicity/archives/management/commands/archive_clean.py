from django.core.management.base import AppCommand
from optparse import make_option
from djangoplicity.archives.management.utils import get_archive_models, clean_archive
import os


class Command(AppCommand):
    args = '<app ...>'
    help = 'Removes unreferenced files from archives'
    option_list = AppCommand.option_list + (
        make_option('-n', '--dry-run',
            action='store_true',
            dest='dryrun',
            default=False,
            help="Don't remove anything"),
        make_option('-c', '--class',
            action='store',
            dest='cls',
            default=None,
            help="Model name to remove unreferenced files from"),
        make_option('-r', '--media-root',
            action='store',
            dest='media_root',
            metavar='DIR',
            default=None,
            help="Override media root from settings.py"),
        make_option('-b', '--backup',
            action='store',
            dest='backup',
            metavar='DIR',
            default=None,
            help="Backup files instead of removing them"),
    )

    def handle_app( self, app, **options ):
        models = get_archive_models( app, cls=options['cls'] )

        if options['media_root'] and os.path.exists( options['media_root'] ):
            from django.conf import settings
            settings.MEDIA_ROOT = options['media_root']

        for m in models:
            clean_archive( m, cls=options['cls'], dryrun=options['dryrun'], backup=options['backup'] )
