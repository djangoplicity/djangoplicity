# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from datetime import datetime, tzinfo, timedelta
import time
from django.conf import settings


class UTCTzInfo( tzinfo ):
    """ UTC Time Zone """

    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return timedelta(0)

utc = UTCTzInfo()


def timetuple_to_datetime( dt ):
    """
    Convert a timetuple (time.struct_time) into a
    naive datetime.datetime object (ie. a datetime
    object without timezone information).
    """
    if isinstance( dt, time.struct_time ):
        return datetime( dt.tm_year, dt.tm_mon, dt.tm_mday, dt.tm_hour,
                dt.tm_min, dt.tm_sec )
    else:
        raise Exception( "Found %s but expected time.struct_time object" % type(dt) )


def timestring_to_seconds( timestring):
    """ converts 'H:m:s:f' string to seconds """
    h, m, s, _f = map(int, timestring.split(':'))
    seconds = (h * 60 * 60) + (m * 60) + s
    return seconds


def timezone( dt, tz='Europe/Berlin' ):
    """
    Convert datetime on local time into datetime in specific timezone
    """
    import pytz

    if not dt:
        return None

    if not dt.tzinfo:
        localtz = pytz.timezone( settings.TIME_ZONE )
        dt = localtz.localize( dt )

    newtz = pytz.timezone( tz )
    dt = newtz.normalize( dt.astimezone( newtz ) )

    return dt
