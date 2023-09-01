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


class Bz2Type(FileType):
    verbose_name = ugettext_noop(u'BZip2 archive (.bz2)')
    exts = ['bz2']
    content_type = 'application/x-bzip2'


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


class TarType(FileType):
    verbose_name = ugettext_noop(u'Tarball (.tar)')
    exts = ['tar']
    content_type = 'application/x-tar'


class TarGzType(FileType):
    verbose_name = ugettext_noop(u'Gzip Tarball Archive (.tar.gz)')
    exts = ['tar.gz']
    content_type = 'application/gzip'


class TarBz2Type(FileType):
    verbose_name = ugettext_noop(u'Bz2 Tarball Archive (.tar.bz2)')
    exts = ['tar.bz2']
    content_type = 'application/x-bzip2'


class TzType(FileType):
    verbose_name = ugettext_noop(u'Compressed Tarball (.tz)')
    exts = ['tz']
    content_type = 'application/x-tar'
