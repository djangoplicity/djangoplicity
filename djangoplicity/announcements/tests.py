from datetime import datetime

from djangoplicity.announcements.models import Announcement, WebUpdate, WebUpdateType, AnnouncementType
from djangoplicity.announcements.serializers import AnnouncementSerializer, WebUpdateSerializer, \
    ICalAnnouncementSerializer, ICalWebUpdateSerializer
from djangoplicity.test.testcases import AdminTestCase
from djangoplicity.announcements.options import AnnouncementOptions, WebUpdateOptions
from django.core import mail
try:
    from mock import patch, MagicMock
except ImportError:
    from unittest.mock import patch, MagicMock


class AnnouncementsTestCase(AdminTestCase):
    conf = {
        'announcements': {
            'root': '/announcements/',
            'options': AnnouncementOptions,
            'list_views': [
                ('embargo', '', 200),
                ('staging', '', 200),
                ('year', '2020/', 200),
            ]
        },
        'webupdates': {
            'root': '/announcements/webupdates/',
            'options': WebUpdateOptions,
            'list_views': []
        }
    }

    def test_index_root(self):
        for conf in list(self.conf.values()):
            response = self.client.get(conf['root'])
            self.assertEqual(response.status_code, 200)

    def test_queries(self):
        for conf in list(self.conf.values()):
            options = conf['options']
            root = conf['root']
            views = conf['list_views']

            for query, subpart, code in views:
                view_url_root = "%sarchive/%s/%s" % (root, query, subpart)
                response = self.client.get(view_url_root)
                self.assertEqual(response.status_code, code)

                for browser in getattr(options.Queries, query).browsers:
                    view_url = "%s%s/" % (view_url_root, browser)
                    response = self.client.get(view_url)
                    self.assertEqual(response.status_code, code)


class ModelsTestCase(AdminTestCase):
    fixtures = ['media', 'announcements']

    def test_web_update_type_model(self):
        web_update_type = WebUpdateType.objects.first()
        self.assertEqual(str(web_update_type), 'type1')

    def test_web_update_model(self):
        web_update = WebUpdate.objects.first()
        self.assertEqual(str(web_update), 'web-update-1: Test Web Update')
        self.assertEqual(web_update.get_absolute_url(), 'https://www.djangoplicity.com/web-update-1')

    def test_announcement_type_model(self):
        ann_type = AnnouncementType.objects.first()
        self.assertEqual(str(ann_type), 'public announcement')

    def test_announcement_model(self):
        """
        Test Announcements methods and attributes
        """
        with self.settings(ARCHIVE_EMBARGO_LOGIN=('embargo', 'mp4preNsa')):
            # The fixture announcement has image main visual, video main visual and comparison main visual
            ann = Announcement.objects.get(id='test-ann')
            image_comparison = ann._get_main_imagen_comparison()

            self.assertEqual(str(ann), 'test-ann: Test Announcement')
            self.assertEqual(str(ann.main_visual), 'Test Image 1')
            self.assertEqual(str(image_comparison), 'Image Comparison 1')
            self.assertEqual(ann.get_embargo_login(), ('embargo', 'mp4preNsa'))
            self.assertEqual(ann.get_absolute_url(), '/announcements/test-ann/')

            # Remove image main visual set
            for img in ann.announcementimage_set.all():
                img.main_visual = False
                img.save()
            del ann._main_visual_cache
            self.assertEqual(str(ann.main_visual), 'Image Comparison 1')

            # Remove image comparison main visual set
            for img in ann.announcementimagecomparison_set.all():
                img.main_visual = False
                img.save()
            del ann._main_visual_cache
            self.assertEqual(str(ann.main_visual), 'Test Video 1')

            # Remove videos main visual set
            for img in ann.announcementvideo_set.all():
                img.main_visual = False
                img.save()
            del ann._main_visual_cache
            self.assertIsNone(ann.main_visual)

            result = Announcement.objects.filter(release_date__lte=datetime.now(), published=True)
            self.assertEqual(str(result.first()), 'test-ann: Test Announcement')

    @patch('djangoplicity.archives.base.ArchiveModel.rename')
    def test_announcement_rename(self, archive_rename_mock):
        """
        Test Announcement rename
        """
        with self.settings(ANNOUNCEMENT_RENAME_NOTIFY=['notity@test.com'], DEFAULT_FROM_EMAIL='noreply@test.com'):
            ann = Announcement.objects.get(id='test-ann')
            ann.rename('new-name')
            self.assertTrue(archive_rename_mock.called)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject,
                             'Announcement renamed: test-ann -> new-name')


class SerializersTestCase(AdminTestCase):
    fixtures = ['media', 'announcements']

    def test_announcement_serializer(self):
        ann = Announcement.objects.get(id='test-ann')
        # Serializer methods
        serializer = AnnouncementSerializer().serialize(ann)
        obj_serialize = serializer.data

        ical_serialize = ICalAnnouncementSerializer().serialize(ann)
        ical_obj_serialize = ical_serialize.data
        self.assertEqual(obj_serialize['title'], 'Test Announcement')
        self.assertEqual(ical_obj_serialize.keys(), ['dtstamp', 'dtend', 'dtstart', 'description', 'summary'])

    def test_web_update_serializer(self):
        web_update = WebUpdate.objects.first()
        # Serializer methods
        serializer = WebUpdateSerializer().serialize(web_update)
        obj_serialize = serializer.data

        ical_serialize = ICalWebUpdateSerializer().serialize(web_update)
        ical_obj_serialize = ical_serialize.data

        self.assertEqual(obj_serialize['title'], 'Test Web Update')
        self.assertEqual(ical_obj_serialize.keys(), ['dtstamp', 'dtend', 'dtstart', 'description', 'summary'])
