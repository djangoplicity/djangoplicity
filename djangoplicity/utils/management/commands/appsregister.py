# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Load and execute register modules in installed apps"
    requires_system_checks = True

    def handle(self, **options ):
        import warnings
        warnings.warn( "Use of appsregister have been deprecated. Please use South data migrations instead.", DeprecationWarning )

        for app in settings.INSTALLED_APPS:
            try:
                __import__("%s.appregister" % app)
                print "Found appregister in %s" % app
            except ImportError:
                continue
