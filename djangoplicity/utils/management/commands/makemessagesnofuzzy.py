# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>

from django.core.management.commands.makemessages import Command as DjangoCommand


class Command(DjangoCommand):
    msgmerge_options = ['-N', '-q']
    msgattrib_options = ['--no-fuzzy', '--no-obsolete']
