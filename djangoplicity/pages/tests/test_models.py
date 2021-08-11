from datetime import datetime, timedelta
from django.test import TestCase
from factories import SectionFactory, PageFactory, URLFactory, PageGroupFactory, EmbeddedPageKeyFactory
from djangoplicity.pages.models import (
    Page, URL, EmbeddedPageKey, Section,
    register_page_key, generate_page_id, page_cache_invalidator,
    url_cache_invalidator, page_key_cache_invalidator, section_cache_invalidator
)


class SectionTest(TestCase):

    def test_unicode_representation(self):
        section = SectionFactory.build()
        self.assertEqual(section.__str__(), 'TestingSection')


class PageTest(TestCase):

    def test_unicode_representation(self):
        page = PageFactory.build()
        self.assertEqual(page.__str__(), 'TestingTitle')

    def test_is_online(self):
        page = PageFactory.build()

        page.published = False
        self.assertFalse(page.is_online())

        page.published = True
        self.assertTrue(page.is_online())

        page.start_publishing = datetime.now() + timedelta(days=1)
        self.assertFalse(page.is_online())
        page.start_publishing = None

        page.end_publishing = datetime.now() - timedelta(days=1)
        self.assertFalse(page.is_online())
        page.end_publishing = None

    def test_get_absolute_url(self):
        translatedPage = PageFactory.create()
        translatedPage.source = PageFactory.create()
        self.assertIsNotNone(translatedPage.get_absolute_url())

        translatedPage.source = None
        self.assertIsNotNone(translatedPage.get_absolute_url())

    def test_save(self):
        section = SectionFactory.build()
        section.save()
        page = PageFactory.build()
        page.script = '<script></script>'
        page.section = section
        page.save()

        self.assertFalse(page.live_edit)

    def test_test_render_errors(self):
        page = PageFactory.build()
        page.test_render_errors()


class URLTest(TestCase):
    def test_unicode_representation(self):
        url = URLFactory.build()
        self.assertEqual(url.__str__(), 'http://someurl.com')


class PageGroupTest(TestCase):
    def test_unicode_representation(self):
        page_group = PageGroupFactory.build()
        self.assertEqual(page_group.__str__(), 'TestingName')


class EmbeddedPageKeyTest(TestCase):
    def test_unicode_representation(self):
        page_key = EmbeddedPageKeyFactory.build()
        self.assertEqual(page_key.__str__(), '{} ({})'.format(page_key.title, page_key.page_key))


class RegisterPageKeyTest(TestCase):
    def test_raise_improperly_configured_except(self):
        EmbeddedPageKeyFactory.create()
        self.assertIsNone(register_page_key('testingApp', 'nonExistsKey'))


class PageSignalsTest(TestCase):

    def test_generate_page_id(self):
        section = SectionFactory.build()
        section.save()
        page = PageFactory.build()
        page.section = section
        page.save()
        page.id = None

        self.assertIsNone(generate_page_id(Page, page, None, True))
        self.assertIsNone(generate_page_id(Page, page, None, False))

    def test_page_cache_invalidator(self):
        section = SectionFactory.build()
        section.save()
        page = PageFactory.build()
        page.section = section
        page.embedded = True
        page.url = 'http://example.com'
        page.save()
        self.assertIsNone(page_cache_invalidator(Page, page, None, True))
        self.assertIsNone(page_cache_invalidator(Page, page, None, False))
        page.embedded = False
        new_page = PageFactory.create()
        new_page.url = 'http://example.com'
        new_page.id = '123'
        page.source_id = '123'
        page.source = new_page
        self.assertIsNone(page_cache_invalidator(Page, page, None, False))


class URLSignalsTest(TestCase):

    def test_url_cache_invalidator(self):
        url = URLFactory.build()
        self.assertIsNone(url_cache_invalidator(URL, url, None, False))
        self.assertIsNone(url_cache_invalidator(URL, url, None, True))


class EmbeddedPageKeySignalsTest(TestCase):

    def test_page_key_cache_invalidator(self):
        page_key = EmbeddedPageKeyFactory.build()
        self.assertIsNone(page_key_cache_invalidator(EmbeddedPageKey, page_key, None, True))


class SectionSignalsTest(TestCase):
    def test_section_cache_invalidator(self):
        section = SectionFactory.build()
        page = PageFactory.build()
        page.section = section
        page.embedded = True

        self.assertIsNone(section_cache_invalidator(Section, section, None, True))
        self.assertIsNone(section_cache_invalidator(Section, section, None, False))
