# coding: utf-8
#
# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
#
from datetime import datetime, timedelta
from django.test import override_settings
import djangoplicity.archives as package
from djangoplicity.announcements.models import Announcement, AnnouncementImage, AnnouncementProxy
from djangoplicity.archives.base import resource_deletion_handler, ArchiveModel
from djangoplicity.archives.resources import ImageResourceManager
from django.db import models
from djangoplicity.media.models.images import Image
from djangoplicity.test.base_tests import BasicTestCase
from django.http import HttpRequest
from django.template import RequestContext, Template
import os
from djangoplicity.archives.contrib import types

try:
    from mock import patch, MagicMock, PropertyMock
except ImportError:
    from unittest.mock import patch, MagicMock, PropertyMock


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'djangoplicity', 'templates'),
            os.path.join(BASE_DIR, 'test_project', 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': True,
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'djangoplicity.archives.context_processors.internal_request',
            ],
        },
    },
]


class ArchiveContextProcessorTestCase(BasicTestCase):

    @override_settings(TEMPLATES=TEMPLATES, INTERNAL_IPS=['127.0.0.1'])
    def test_context_processors(self):
        """
        Test archive context processor, identify in a template this is INTERNAL REQUEST
        """
        request = HttpRequest()
        request.user = self.admin_user
        request.META['REMOTE_ADDR'] = '127.0.0.1'

        context = RequestContext(request, {})
        template = Template("{% if INTERNAL_REQUEST %}Is Internal{% endif %}").render(context)
        self.assertEqual(template, 'Is Internal')


class ArchiveInitTestCase(BasicTestCase):

    @override_settings(USE_I18N=False)
    def test_init_archive_app(self):
        cache_key = package._gen_cache_key('public_', 'archive', 5555, 'help')
        self.assertEqual(cache_key, 'public__7617057745003194269_5555_help')


class ArchiveBaseTestCase(BasicTestCase):
    fixtures = ['media', 'announcements']

    @override_settings(ARCHIVE_AUTO_RESOURCE_DELETION=True)
    @patch('shutil.move')
    @patch('os.makedirs')
    @patch('os.remove')
    def test_archive_resource_deletion_handler(self, os_remove, os_make_dir_mock, os_move_file_mock):
        # Class hack to handler file resources
        class FileResource:
            def __init__(self):
                self.path = 'archive/test_file.tiff'
                self.name = 'test_file.tiff'

        # Class not inherited from ArchiveModel class
        class NotSubclassArchiveModel:
            def __init__(self):
                pass

        # ArchiveModel Subclass to tester methods where
        # Delete the files instead of moving them to Trash
        class TestArchiveModel(ArchiveModel, models.Model):
            id = models.SlugField(primary_key=True, max_length=10)
            title = models.CharField()

            class Meta:
                app_label = 'test_project'

            class Archive:
                original = ImageResourceManager(type=types.OriginalImageType)

                class Meta:
                    root = 'archives/testing/'
                    release_date = True
                    embargo_date = True
                    release_date_owner = True
                    last_modified = True
                    created = True
                    published = True
                    delete_instead_of_copy = True

        # Test None return by invalid sender
        image = Image.objects.get(id='image-1')
        response = resource_deletion_handler(sender=NotSubclassArchiveModel, instance=image)
        self.assertIsNone(response)

        # Test valid Sender Methods
        instance = TestArchiveModel()
        # hack to get resource for the specified resource_name.
        instance._resource_cache = {'original': FileResource()}
        resource_deletion_handler(sender=TestArchiveModel, instance=instance)

        self.assertTrue(os_remove.called)
        os_remove.assert_called_with('archive/test_file.tiff')

        # Moving the files to Trash  instead of delete
        instance.Archive.Meta.delete_instead_of_copy = False
        resource_deletion_handler(sender=TestArchiveModel, instance=instance)
        self.assertTrue(os_make_dir_mock.called)
        self.assertTrue(os_move_file_mock.called)

    @override_settings(USE_I18N=True)
    def test_rename_archive(self):
        # validate archive rename
        instance = Image.objects.get(id='image-1')
        ann = Announcement.objects.get(id='test-ann')
        # Add Translations
        translation = {
            'id': 'test-ann-es',
            'source': ann,
            'published': True,
            'lang': 'es',
            'description': 'this is a translation',
            'subtitle': 'Translation subtitle',
            'title': 'Ann test translate',
            'translation_ready': True
        }
        AnnouncementProxy.objects.create(**translation)

        with self.assertRaises(Exception):
            instance.rename(new_pk='image-2')

        instance.rename(new_pk='test-ann-image')

        ann_image = ann.announcementimage_set.get(archive_item_id='test-ann-image')
        self.assertIsInstance(ann_image, AnnouncementImage)

        # When rename an announcement or press release the related resources the id must be start with the new pk
        ann.rename(new_pk='new-test-ann')
        instance = Image.objects.get(id='new-test-ann-image')

        related_announcement = instance.announcement_set.get(id='new-test-ann')
        self.assertIsInstance(related_announcement, Announcement)

    @patch('shutil.rmtree')
    def test_delete_resources(self, delete_file_mock):
        """ Delete all resources """
        with patch('djangoplicity.media.models.images.Image.resource_original', new_callable=PropertyMock) as patched_property:
            class FileResource:
                def __init__(self):
                    self.path = 'archives/original/test_file.tiff'
                    self.name = 'test_file.tiff'

            patched_property.return_value = FileResource()
            instance = Image.objects.get(id='image-1')

            instance.delete_resources()
            self.assertTrue(delete_file_mock.called)
            delete_file_mock.assert_called_with('archives/original/test_file.tiff')

    @patch('os.rename')
    def test_move_resources(self, os_rename_mock):
        """ Move all resources """
        with patch('djangoplicity.media.models.images.Image.resource_original', new_callable=PropertyMock) as patched_property:
            class FileResource:
                def __init__(self):
                    self.path = 'archives/original/test_file.tiff'
                    self.name = 'test_file.tiff'

            patched_property.return_value = FileResource()
            instance = Image.objects.get(id='image-1')

            instance.move_resources('image-1')
            self.assertTrue(os_rename_mock.called)

    @patch('djangoplicity.archives.contrib.social.tasks.facebook_refresh.delay')
    @patch('djangoplicity.archives.contrib.security.StaticFilesProtectorCache.run_async')
    def test_archive_miscellaneous_methods(self, static_files_protector_cache_mock, facebook_refresh_mock):
        instance = Image.objects.get(id='image-1')
        # Test List of resources that should not be overwritten
        self.assertEqual(instance.locked_resources(), [])
        instance.keep_newsfeature = True
        locked_resources = instance.locked_resources()
        self.assertEqual(locked_resources, ['banner1920', 'newsfeature', 'potwmedium', 'thumb350x'])

        # Test Called at the time defined by embargo_date
        instance.embargo_date_action()
        self.assertTrue(static_files_protector_cache_mock.called)

        # Test Called at the time defined by release_date
        instance.release_date_action()
        self.assertTrue(facebook_refresh_mock.called)
        facebook_refresh_mock.assert_called_with('example.com/images/image-1/')

        # Test the task to run embargo_date_action
        instance.embargo_task_id = 'a85bedd6-37aa-4363-b149-93f0c18ed159'
        instance.embargo_date = datetime.now() + timedelta(weeks=1)
        instance.set_embargo_date_task()

        self.assertNotEqual(instance.embargo_task_id, 'a85bedd6-37aa-4363-b149-93f0c18ed159')
