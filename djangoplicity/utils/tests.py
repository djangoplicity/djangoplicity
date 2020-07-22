# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from djangoplicity.utils import datetimes
from datetime import datetime
from django.test import TestCase
from django.conf import settings

class TestDatetimes(TestCase):
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


        assert timezone(est, 'Europe/Berlin').isoformat() == '2011-03-10T12:00:00+01:00'
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

class UtilsTestCase(TestCase):
    def test_videothumbnails(self):
        from djangoplicity.utils import videothumbnails
        self.assertRaises(ValueError, videothumbnails.readexif, 'f', 'tags')
        self.assertEqual(videothumbnails.decode_duration("20:20"), (1220, 0))
        self.assertEqual(videothumbnails.format_duration(100), "00:01:40")
        self.assertEqual(videothumbnails.create_video_thumbnail("something", 200), "something.png")

    def test_text(self):
        from djangoplicity.utils import text
        self.assertEqual(text.named_entities(UnicodeEncodeError("utf-8", unicode("hola"), 1, 2, "yes" )), (u'&#111;', 2))

    def test_storage(self):
        from djangoplicity.utils import storage
        pipe_instance = storage.PipelineManifestStorage("a mixin?", "a storage?")
        self.assertIsInstance(pipe_instance, storage.PipelineManifestStorage)

    def test_pagination(self):
        from djangoplicity.utils import pagination
        from django.urls import NoReverseMatch

        class PagObj:
            def __init__(self):
                self.number = 1
        
        self.assertEqual(pagination._adj_range(1, PagObj(), [1, 3]), [1, 3])

        paginator = pagination.Paginator()
        self.assertRaises(NoReverseMatch, paginator.paginate, 100)

    def test_optionparser(self):
        from djangoplicity.utils import optionparser
        self.assertIsNot(optionparser.get_options([
        ( 'a', 'app', 'Django app used for creating the directories', False, { 'default' : '' } ),
        ( 'o', 'output', 'Output directory', False, { 'default' : settings.MEDIA_ROOT } ),
        ( 'i', 'import', 'Output directory for import dirs', False, { 'default' : settings.ARCHIVE_IMPORT_ROOT } ),
        ( 'm', 'model', 'Specific archive model', False ),
        ( 'n', 'dry-run', 'Do not actually create the directories', False, { 'action' : 'store_true', 'default' : False } )     
    ]), "")

    def test_logger(self):
        from djangoplicity.utils import logger
        the_logger = logger.define_logger( "migration_logger", file_logging=False )
        self.assertNotIsInstance(the_logger, TestCase)

