# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>

import six
from datetime import timedelta, date as pdate
from dateutil.parser import parse

from django.conf import settings
from django import template
from django.template.defaultfilters import stringfilter, date
from django.utils.dateformat import format
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter( name='timezone' )
def timezone( value, arg='Europe/Berlin' ):
    """
    Converts a datetime from one timezone to another timezone.

    Uses the settings.TIME_ZONE as timezone for input value, if
    datetime not already have a timezone.
    """
    if not value:
        return u''

    try:
        import pytz

        if not value.tzinfo:
            localtz = pytz.timezone( settings.TIME_ZONE )
            value = localtz.localize( value )

        newtz = pytz.timezone( arg )
        value = newtz.normalize(value.astimezone( newtz ))

        return value
    except ImportError:
        return value


@register.filter( name='time4lang')
def time4lang(value, arg=settings.LANGUAGE_CODE):
    """
    Converts a datetime frome one tz to another tz. takes the language as input
    """
    try:
        if not value:
            return u''

        timezones = {}
        if hasattr(settings, 'LANGUAGE_TIMEZONE'):
            timezones = dict(settings.LANGUAGE_TIMEZONE)

        if arg in timezones:
            return timezone(value, timezones[arg])
        else:
            return timezone(value)
    except Exception, e:
        return e.message


@register.filter( name='datetime' )
def datetime( value, arg=None ):
    """ wrapper around 'date' default filter """

    if not value:
        return u''

    # Try to convert value to datetime if it is a string
    if isinstance(value, six.string_types):
        value = parse(value)

    if arg is None:
        arg = 'DATETIME'

    fmt = "%s_FORMAT" % arg

    dt = date(value, fmt)

    if value.tzinfo and hasattr(value.tzinfo, '_tzname'):
        tz = value.strftime(' %Z')

        # There is no strict concensus as to whether Australia/Canberra is
        # called EST or AEST, see e.g.:
        # http://www.bom.gov.au/climate/averages/tables/daysavtm.shtml As EST
        # can be confused with the US EST we overwrite the tzdatabase default
        # and use AEST and ADST instead:

        if str(value.tzinfo) == 'Australia/Canberra' and tz == ' EST':
            tz = ' AEST'
        if str(value.tzinfo) == 'Australia/Canberra' and tz == ' DST':
            tz = ' ADST'

        # Some locales have the timezone by default,
        # so we remove it before we add it back
        if dt.endswith(tz):
            dt = dt[:-len(tz)]

        # Add the timezone with a link to timeanddate.com
        tz = tz.strip()
        tz = ' <a href="http://www.timeanddate.com/time/zones/%s" target="_blank">%s</a>' % (tz.lower(), tz)
        dt += tz
        dt = mark_safe(dt)

    return dt


@register.filter( name='isodt' )
@stringfilter
def isodt( value ):
    """ wrapper around 'date' default filter """
    return parse( value )


@register.simple_tag
def current_month():
    '''
    Return the current month (1-12)
    '''
    return pdate.today().month


@register.filter( name='datetime_old' )
def datetime_old( value, arg=None ):
    """
    DEPRECATED: please use datetime instead.

    Formats a date according to DATETIME_FORMAT setting or
    a different setting specified in the argument.

    Example::
        {% load djangoplicity_datetime %}
        {{ date_published|datetime }}

        equals

        {{ date_published|datetime:"DATETIME" }}

        If you want to use a different format from the settings
        file add it as an argument.

        {{ date_published|datetime:"DATETIME" }}
        {{ date_published|datetime:"DATETIME_LONG" }}

        Not you settings should contain format above specifications:

        DATETIME_FORMAT = "..."
        DATETIME_LONG_FORMAT = "..."
    """
    if not value:
        return u''

    if arg is None:
        arg = 'DATETIME'

    try:
        arg = getattr( settings, "%s_FORMAT" % arg )
    except AttributeError:
        arg = settings.DATETIME_FORMAT

    return format( value, arg )


@register.filter( name='timesub' )
def timesub( value, arg=0 ):
    """ Substrict 'arg' hours from value """
    return value - timedelta(hours=1)
