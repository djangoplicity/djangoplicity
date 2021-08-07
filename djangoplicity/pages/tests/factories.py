import factory
from djangoplicity.pages.models import (
    Page, PageGroup, Section, URL, EmbeddedPageKey, PageProxy)


class SectionFactory(factory.Factory):
    class Meta:
        model = Section

    name = 'TestingSection'

class PageFactory(factory.Factory):
    class Meta:
        model = Page
    
    title = 'TestingTitle'
    section = factory.SubFactory(SectionFactory)

class URLFactory(factory.Factory):
    class Meta:
        model = URL

    url = 'http://someurl.com'


class PageGroupFactory(factory.Factory):
    class Meta:
        model = PageGroup

    name = 'TestingName'


class EmbeddedPageKeyFactory(factory.Factory):
    class Meta:
        model = EmbeddedPageKey
    
    title = 'TestingTitle'
    page_key = 'TestingPageKey'

