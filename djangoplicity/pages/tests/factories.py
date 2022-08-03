import factory
from djangoplicity.pages.models import (
    Page, PageGroup, Section, URL, EmbeddedPageKey, PageProxy)


class SectionFactory(factory.Factory):
    name = 'TestingSection'

    class Meta:
        model = Section


class PageFactory(factory.Factory):
    title = 'TestingTitle'
    section = factory.SubFactory(SectionFactory)

    class Meta:
        model = Page


class URLFactory(factory.Factory):
    url = 'http://someurl.com'

    class Meta:
        model = URL


class PageGroupFactory(factory.Factory):
    name = 'TestingName'

    class Meta:
        model = PageGroup


class EmbeddedPageKeyFactory(factory.Factory):
    title = 'TestingTitle'
    page_key = 'TestingPageKey'

    class Meta:
        model = EmbeddedPageKey
