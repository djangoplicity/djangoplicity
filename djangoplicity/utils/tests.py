# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from djangoplicity.utils import datetimes
from datetime import datetime

from django.conf import settings

class TestDatetimes:
    def test_timestring_to_seconds(self):
        """ test correct conversion of H:m:s:f to seconds """
        time = '10:30:40:0'
        seconds = (10 * 60 * 60) + (30 * 60) + 40
        
        calculated_seconds = datetimes.timestring_to_seconds(time)
        assert seconds == calculated_seconds

    def test_timezone(self):
        """ test conversion of local time to specific timezone """
        settings.TIME_ZONE = 'Europe/Berlin'

        from djangoplicity.utils.templatetags.djangoplicity_datetime import timezone

        est = datetime(2011, 3, 10, 12, 00 ) # Eastern Standard Time
        edt = datetime(2011, 3, 15, 12, 00 ) # Eastern Daylight Time
        cet = datetime(2011, 3, 24, 12, 00 ) # Central European Time
        cest = datetime(2011, 3, 30, 12, 00 ) # Central European Summer Time


        assert timezone(est, 'Europe/Berlin').isoformat() == '2011-06-10T12:00:00+01:00'
        assert timezone(edt, 'Europe/Berlin').isoformat() == '2011-03-15T12:00:00+01:00'
        assert timezone(cet, 'Europe/Berlin').isoformat() == '2011-03-24T12:00:00+01:00'
        assert timezone(cest, 'Europe/Berlin').isoformat() == '2011-03-30T12:00:00+02:00'

        assert timezone(est, 'US/Eastern').isoformat() == '2011-03-10T06:00:00-05:00'
        assert timezone(edt, 'US/Eastern').isoformat() == '2011-03-15T07:00:00-04:00'
        assert timezone(cet, 'US/Eastern').isoformat() == '2011-03-24T07:00:00-04:00'
        assert timezone(cest, 'US/Eastern').isoformat() == '2011-03-30T06:00:00-04:00'

    def test_time4lang(self):
        settings.TIME_ZONE = 'Europe/Berlin'
        settings.LANGUAGE_TIMEZONE = {
            'pt-br': 'America/Sao_Paulo',
        }

        from djangoplicity.utils.templatetags.djangoplicity_datetime import time4lang

        # Transitions
        # Diff: -3
        # BRST -> BRT: 2011/02/20
        # Diff: -4
        # CET -> CEST: 2011/03/27
        # Diff: -5
        # BRT -> BRST: 2011/10/16
        # Diff: -4
        # CEST -> CET: 2011/10/30
        # Diff: -3

        brst = datetime(2011, 2, 18, 12, 00) # Brasilia Summer Time
        brt = datetime(2011, 2, 22, 12, 00) # Brasilia Time
        cet = datetime(2011, 3, 24, 12, 00) # Central European Time
        cest = datetime(2011, 3, 30, 12, 00) # Central European Summer Time
        cest_brst = datetime(2011, 10, 18, 12, 00)
        cet_brst = datetime(2011, 11, 01, 12, 00)

        assert time4lang(brst, 'pt-br').isoformat() == '2011-02-18T09:00:00-02:00'
        assert time4lang(brt, 'pt-br').isoformat() == '2011-02-22T08:00:00-03:00'
        assert time4lang(cet, 'pt-br').isoformat() == '2011-03-24T08:00:00-03:00'
        assert time4lang(cest, 'pt-br').isoformat() == '2011-03-30T07:00:00-03:00'
        assert time4lang(cest_brst, 'pt-br').isoformat() == '2011-10-18T08:00:00-02:00'
        assert time4lang(cet_brst, 'pt-br').isoformat() == '2011-11-01T09:00:00-02:00'
