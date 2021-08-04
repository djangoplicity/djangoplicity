# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>


from django.utils.translation import ugettext_noop
from djangoplicity.archives.resources import FileType



class DmgType(FileType):
    verbose_name = ugettext_noop(u'Apple Disk Image (.dmg)')
    exts = ['dmg']
    content_type = 'application/octet-stream'


class ExeType(FileType):
    verbose_name = ugettext_noop(u'Microsoft Application (.exe)')
    exts = ['exe']
    content_type = 'application/x-msdownload'


class DebType(FileType):
    verbose_name = ugettext_noop(u'Debian Package (.deb)')
    exts = ['deb']
    content_type = 'application/x-debian-package'


class RpmType(FileType):
    verbose_name = ugettext_noop(u'Redhat package (.rpm)')
    exts = ['rpm']
    content_type = 'application/x-redhat-package-manager'


class SnapType(FileType):
    verbose_name = ugettext_noop(u'Snap Application (.snap)')
    exts = ['snap']
    content_type = 'application/octet-stream'
