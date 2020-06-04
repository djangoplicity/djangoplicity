# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

try:
    from django.utils import unittest
except ImportError:
    import unittest
from datetime import datetime


class TemplateTagDatetimeTest( unittest.TestCase ):

    #def test_timezone(self):
    #   response = self.client.get('/customer/details/')
    #   self.assertEqual(response.status_code, 200)

    def test_timezone(self):
        from django.conf import settings
        settings.TIME_ZONE = 'Europe/Berlin'
        from djangoplicity.utils.templatetags.djangoplicity_datetime import timezone

        est = datetime(2011, 3, 10, 12, 00 )
        edt = datetime(2011, 3, 15, 12, 00 )
        cet = datetime(2011, 3, 24, 12, 00 )
        cest = datetime(2011, 3, 30, 12, 00 )

        self.assertEqual( timezone( est, 'Europe/Berlin' ).isoformat(), '2011-03-10T12:00:00+01:00' )
        self.assertEqual( timezone( edt, 'Europe/Berlin' ).isoformat(), '2011-03-15T12:00:00+01:00' )
        self.assertEqual( timezone( cet, 'Europe/Berlin' ).isoformat(), '2011-03-24T12:00:00+01:00' )
        self.assertEqual( timezone( cest, 'Europe/Berlin' ).isoformat(), '2011-03-30T12:00:00+02:00' )

        self.assertEqual( timezone( est, 'US/Eastern' ).isoformat(), '2011-03-10T06:00:00-05:00' )
        self.assertEqual( timezone( edt, 'US/Eastern' ).isoformat(), '2011-03-15T07:00:00-04:00' )
        self.assertEqual( timezone( cet, 'US/Eastern' ).isoformat(), '2011-03-24T07:00:00-04:00' )
        self.assertEqual( timezone( cest, 'US/Eastern' ).isoformat(), '2011-03-30T06:00:00-04:00' )

    def test_time4lang( self ):
        from django.conf import settings
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

        brst = datetime(2011, 2, 18, 12, 00)
        brt = datetime(2011, 2, 22, 12, 00)
        cet = datetime(2011, 3, 24, 12, 00)
        cest = datetime(2011, 3, 30, 12, 00)
        cest_brst = datetime(2011, 10, 18, 12, 00)
        cet_brst = datetime(2011, 11, 01, 12, 00)

        self.assertEqual( time4lang(brst, 'pt-br').isoformat(), '2011-02-18T09:00:00-02:00')
        self.assertEqual( time4lang(brt, 'pt-br').isoformat(), '2011-02-22T08:00:00-03:00')
        self.assertEqual( time4lang(cet, 'pt-br').isoformat(), '2011-03-24T08:00:00-03:00')
        self.assertEqual( time4lang(cest, 'pt-br').isoformat(), '2011-03-30T07:00:00-03:00')
        self.assertEqual( time4lang(cest_brst, 'pt-br').isoformat(), '2011-10-18T08:00:00-02:00')
        self.assertEqual( time4lang(cet_brst, 'pt-br').isoformat(), '2011-11-01T09:00:00-02:00')


if __name__ == "__main__":
    import unittest
    unittest.main()
