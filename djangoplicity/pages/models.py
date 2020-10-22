# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>

from builtins import str
import copy
import datetime

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models import signals
from django.forms import fields
from django.template import Engine, Template
from django.template.base import TemplateSyntaxError
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from djangoplicity.archives.translation import TranslationProxyMixin
from djangoplicity.translation.models import TranslationModel, \
    get_path_for_language

if not hasattr( settings, 'PAGE_TEMPLATE_CHOICES'):
    settings.PAGE_TEMPLATE_CHOICES = ()

CACHE_KEY = {
    'embedded_pages': 'djangoplicity.pages_embedded',
    'pages': 'djangoplicity.pages_',
    'urlindex': 'djangoplicity.pages_urlindex',
    'embedded_page_keys': 'djangoplicity.pages_keys_index',
}


class TemplateField(models.CharField):
    '''
    Custom field to avoid having choices caught by makemigrations
    '''
    def formfield(self, **kwargs):
        choices = [('', '---------')] + list(settings.PAGE_TEMPLATE_CHOICES)
        return fields.ChoiceField(choices=choices, required=False)


@python_2_unicode_compatible
class Section( models.Model ):
    """
    Sections are used to define the templates used for different areas
    of a website.
    """

    name = models.CharField( max_length=100 )
    # Name of the section.

    template = TemplateField(max_length=100)
    # Template to use.

    append_title = models.CharField( max_length=100 )
    # Text to append to title, e.g. '| Title'

    def __str__( self ):
        return self.name

    class Meta:
        ordering = ['name']


@python_2_unicode_compatible
class URL( models.Model ):
    """ URL of page. URLs are unique and can only contain alpha numeric characters. """
    url = models.CharField(_(u'URL'), max_length=200, db_index=True, unique=True,
                            help_text=_(u"Example: '/about/contact/'. Make sure to have leading and trailing slashes. Good and descriptive URLs are important for good user experience and search engine ranking."))
    page = models.ForeignKey('Page', null=True, on_delete=models.CASCADE)

    def __str__( self ):
        return self.url


@python_2_unicode_compatible
class PageGroup( models.Model ):
    '''
    Model to group pages together for access control
    '''
    name = models.CharField(max_length=50, help_text=_('Name of the group'))
    description = models.TextField(blank=True, help_text=_('Description of group'))
    groups = models.ManyToManyField(Group, help_text=_('Groups which have to access to this page group'), blank=True)
    full_access = models.BooleanField(default=False, help_text=_('If checked members of this group have access to all pages'))

    def __str__( self ):
        return self.name


@python_2_unicode_compatible
class Page( TranslationModel ):
    """
    A general purpose module for displaying and editing text on a website.
    """
    #
    # Page content
    #
    id = models.SlugField( primary_key=True, help_text=_(u'ID of page') )

    embedded = models.BooleanField( default=False, help_text=_(u'If checked, the page cannot be viewed through the URL. Used for pages that are embedded into complex pages like the frontpage.') )
    # Pages can be embedded into other views. If a page should not be reachable through a URL because
    # it is embedded into another more complex view, this field should be set to true. Note that
    # the view embedding a page, are free to adhere only to a couple of fields if it wants.

    title = models.CharField( max_length=200, help_text=_(u"Title is shown in browser window. Use a good informative title, since search engines normally display the title on their result pages.") )
    # Title of page, to be displayed in the Title-tag of the page.

    # According to http://www.seomoz.org/article/beginners-1-page#4b and
    # http://www.seomoz.org/article/search-ranking-factors the title is belived to have
    # great impact on the page ranking in search engines. Furthermore the title tag
    # is usually displayed as the result link on search engine result pages, making
    # and important factor for getting users to click the link.

    content = models.TextField( blank=True )
    # The actually content of the page.

    script = models.TextField(blank=True, help_text='Javascript to be included in page footer')

    #
    # Metadata
    #
    description = models.TextField( blank=True, help_text=_(u'The metadata description is normally shown in search engine results, making the description an effective way of capturing users attention. Description should be a clear description of the content and less the 200 characters long. Also used when sharing page on social media') )
    # The description is normally shown in search engine results, making the description
    # an effective way of capturing users attention. Description should be a clear
    # description of the content and less the 200 characters long.

    keywords = models.TextField( blank=True, help_text=_(u'Comma-separated list of keywords for this page. Mainly used internally as search engines rarely use keywords to rank pages.') )
    # A comma-separated list of keywords describing the content of the page.
    # The field has no real effect on search engine ranking, but can be used
    # categorize pages or create tag clouds.

    opengraph_image = models.CharField(_(u'OpenGraph Image'), blank=True, max_length=250,
            help_text=_(u"Example: 'https://www.eso.org/public/archives/imagecomparisons/newsfeature/potw1413a.jpg'. If given: full path to an image that will be used when sharing the page on social media. Must be larger than 200x200px and smaller than 5MB."))

    #
    # Publishing information
    #
    #TODO: Test if this should be blank, null or blank and null
    #TOOD: Automatically populate this field based on
    #author = models.ForeignKey( User, null=True, on_delete=models.CASCADE)
    #""" Author of the page. """

    last_modified = models.DateTimeField( auto_now=True )
    # Date/time of last time page was modified.

    created = models.DateTimeField( auto_now_add=True )
    # Date/time of when page was created.

    published = models.BooleanField( _("Published"), default=True, help_text=_(u'If this is unchecked, the page will not be viewable online. Timed publishing of published pages, can be controlled by the start/end publishing fields.') )
    # Determines if the page is online. Makes it possible to work on pages,
    # without making them available online. Start/end publishing fields only has
    # effect if this field is true.

    start_publishing = models.DateTimeField( null=True, blank=True, help_text=_(u'Leave blank to publish immediately. The field only has effect for published pages (see above).') )
    # Determines when the page should go online. The field only has effect if "published" field is true.

    end_publishing = models.DateTimeField( null=True, blank=True, help_text=_(u'Leave blank for open-ended publishing. The field only has effect for published pages (see above).') )
    # Determines when the page should be take offline. The field only has effect if "published" field is true.

    #
    # Page style
    #
    section = models.ForeignKey( Section, default=1, help_text=_(u'Determines e.g. which templates to use for rendering the template.'), on_delete=models.CASCADE)
    # Section to use for this page. A section determines default values for a page, and the visual layout (e.g. templaes).

    template_name = TemplateField(max_length=100, blank=True, help_text=_(u'Override the template specified by the section.'))
    # Path to template to use for rendering this page. If template is not specified, the sections template will be used.

    #
    # Extra Page style
    #
    # Possible extra pages style options (most could be handle from specifying an specifyc template):
    # -feed
    # -favourites icon
    # -extra javascript

    #
    # Advanced features
    #
    login_required = models.BooleanField( default=False, help_text=_("If checked, only logged-in users will be able to view the page."))
    # If checked page will not be cached.

    #disable_cache = models.BooleanField( default=False, help_text=_("If this is checked, caching of the page will be disable. WARNING: Only check this option if you know what you are doing.") )
    #""" Field can be used to turn of the caching of a page. T """

    #enable_comments = models.BooleanField( default=False )
    #""" Enable commenting of this page. """

    dynamic = models.BooleanField( default=False, help_text=_('If checked, page will not be cached. Use with care!') )
    # Controls the caching of a page. In case dynamic is checked,
    # only the compiled template and not the rendered template will
    # be cached. Use this option, if you want variables in the page
    # to be updated on every request to the page.

    raw_html = models.BooleanField( default=False, help_text=_('If checked the WYSIWYG editor will be disabled, useful for editing pages with javascript.') )
    live_edit = models.BooleanField(default=True, help_text=_('Allow Live edit (only if the page doesn\'t use javascript, embed, etc.)') )

    redirect_url = models.CharField(_(u'Redirect URL'), blank=True, max_length=200, db_index=True,
            help_text=_(u"Example: 'https://www.eso.org/public/'. Used if the page has been permanently moved. If given, access to the page will trigger a HTTP 301 redirection to the given URL."))

    # Groups the page belongs to
    groups = models.ManyToManyField(PageGroup, blank=True, help_text=_('PageGroup the Page belongs to, used for access restriction.'))

    def is_online(self):
        """
        Determine if a page is viewable on the website, meaning that the page must:
            * be published
            * start publishing date/time must have been passed.
            * end publishing date/time must not have been passed.
            * in case of translation, translation_ready but me true
        """
        if not self.published:
            return False
        if self.start_publishing is not None and datetime.datetime.now() < self.start_publishing:
            return False
        if self.end_publishing is not None and datetime.datetime.now() > self.end_publishing:
            return False
        if settings.USE_I18N and self.is_translation():
            return self.translation_ready
        return True
    is_online.boolean = True
    is_online.short_description = _( u'Is Online' )

    def __str__( self ):
        return self.title

    def get_absolute_url(self):
        '''
        As a page can have multiple URLs we return the first one:
        '''
        try:
            if settings.USE_I18N and self.is_translation():
                base_url = self.source.url_set.all()[0].url
            else:
                base_url = self.url_set.all()[0].url
        except IndexError:
            base_url = ''

        return get_path_for_language(self.lang, base_url)

    def save(self, **kwargs):
        '''
        Disable live edit for dynamic pages:
        '''
        if self.script or '{{' in self.content or '{%' in self.content:
            self.live_edit = False

        super(Page, self).save(**kwargs)

    def test_render_errors(self):
        '''
        Tries to render the content, return None if everything is fine
        or the error so it can be displayed in the admin
        '''
        # In production the template Engine has debug set to False, but as
        # we need it to identify any possible rendering errors we copy it
        # and set the copies debug to True
        engine = copy.copy(Engine.get_default())
        engine.debug = True

        try:
            Template(self.content, engine=engine)
        except TemplateSyntaxError as e:
            return e.template_debug

    class Translation:
        fields = ['title', 'content', 'description', 'keywords', ]
        excludes = ['published', 'last_modified', 'created', ]

    class Meta:
        ordering = ['title']
        permissions = (
            ("can_view_inactive", "Can view inactive pages"),
            ("view_elt_pages_only", "Can view only ELT pages"),
        )

    class Archive:
        class Meta:
            clean_html_fields = ['content']


@python_2_unicode_compatible
class EmbeddedPageKey( models.Model ):
    """
    Model for associating a key with a page, so that pages can be
    embedded in other applications without explicitly linking to a
    page id. Allows for also changing which pages are embedded.

    A model register a key with this model, which is then inserted into the table.
    Staff users can the use the admin interface to edit each instance, but can
    however not add new entries.
    """

    application = models.CharField( max_length=255 )
    # Name of application who registered the key.

    page_key = models.SlugField( primary_key=True )
    # Key name - a new key is added

    title = models.CharField( max_length=255, help_text=_('Meaningful title for embedded ') )
    # Meaning full title for embedded page. Default title must be provided by registering application.

    description = models.TextField( blank=True, help_text=_('Description of where the page is being embedded and if there is any special considerations to take - e.g. page length etc.') )
    # Description of where the embedded page will be shown,
    # as well as any specific details that should be taken
    # into consideration editing the related page.

    # Initial description should be provided by the application registering the key.

    page = models.ForeignKey( Page, null=True, blank=True, limit_choices_to={ 'embedded__exact': True }, help_text=_('Select page that you want to use for the specific key. Note, only pages marked as embedded pages can be selected.'), on_delete=models.CASCADE)
    # Page that is to be embedded for the specific key.

    last_modified = models.DateTimeField( auto_now=True )
    # Date/time of last time page was modified.

    def __str__( self ):
        return u'%s (%s)' % (self.title, self.page_key)

    class Meta:
        verbose_name = _('Page Embedding')


# ========================================================================
# Translation proxy model
# ========================================================================
@python_2_unicode_compatible
class PageProxy( Page, TranslationProxyMixin ):
    """
    Page proxy model for creating admin only to edit
    translated objects.
    """
    objects = Page.translation_objects

    def clean( self ):
        # Note: For some reason it's not possible to
        # to define clean/validate_unique in TranslationProxyMixin
        # so we have to do this trick, where we add the methods and
        # call into translation proxy micin.
        self.id_clean()

    def validate_unique( self, exclude=None ):
        self.id_validate_unique( exclude=exclude )

    def __str__( self ):
        return "%s: %s" % ( self.id, self.title )

    class Meta:
        proxy = True
        verbose_name = _('Page translation')

    class Archive:
        class Meta:
            rename_pk = ('pages_page', 'id')
            rename_fks = []
            clean_html_fields = ['content']


def register_page_key( app, key, title='', description='' ):
    """
    Register a page key for an application. The user chosen page
    can later be embedded into any view by using pages.views.embed_page_key()
    """
    try:
        obj = EmbeddedPageKey.objects.get( page_key=key )
        if obj.application != app:
            raise ImproperlyConfigured(_('Application %(app)s failed to register page key "%(key)s". The key has already been registered by the application %(otherapp)s.') % { 'app': app, 'key': key, 'otherapp': obj.application } )
    except EmbeddedPageKey.DoesNotExist:
        EmbeddedPageKey.objects.create( application=app, page_key=key, title=title, description=description, page=None  )


def build_urlindex():
    """
    Build an index, mapping URLs to page ids. The index is used
    for fast lookup of URLs.
    """
    index = dict(
        URL.objects.filter(page__isnull=False)
        .select_related('page')
        .values_list('url', 'page_id')
    )

    cache.set(CACHE_KEY['urlindex'], index)
    return index


def build_page_key_index():
    """
    Build an index, mapping page keys to page ids. The index is used
    for fast lookup of page keys (used by embedded pages).
    """
    qs = EmbeddedPageKey.objects.select_related('page').filter( page__isnull=False )

    index = {}

    for p in qs:
        index[ p.page_key ] = p.page.id

    cache.set( CACHE_KEY['embedded_page_keys'], index )
    return index


def page_cache_invalidator( sender, instance, signal, raw=False, *args, **kwargs ):
    """
    Invalidate the cache of a page, when it is updated/created/deleted
    """
    if raw:
        return

    if instance.embedded:
        cache.delete( CACHE_KEY['embedded_pages'] + str(instance.pk) )
    else:
        if instance.is_source():
            urls = instance.url_set.all()
        else:
            urls = instance.source.url_set.all()
        for url in urls:
            if settings.USE_I18N:
                cache.delete('%s_%s_%s_internal' % (CACHE_KEY['pages'], str(url.url.__hash__()), instance.lang))
                cache.delete('%s_%s_%s_external' % (CACHE_KEY['pages'], str(url.url.__hash__()), instance.lang))
            else:
                cache.delete('%s_%s_internal' % (CACHE_KEY['pages'], str(url.url.__hash__())))
                cache.delete('%s_%s_external' % (CACHE_KEY['pages'], str(url.url.__hash__())))
        build_urlindex()
        build_page_key_index()


def url_cache_invalidator( sender, instance, signal, raw=False, *args, **kwargs ):
    """
    Invalidate the cache of a page, when a url updated/created/deleted
    """
    if raw:
        return
    cache.delete( '%s_%s_internal' % (CACHE_KEY['pages'], str(instance.url.__hash__())) )
    cache.delete( '%s_%s_external' % (CACHE_KEY['pages'], str(instance.url.__hash__())) )
    build_urlindex()
    build_page_key_index()


def page_key_cache_invalidator( sender, instance, signal, raw=False, *args, **kwargs ):
    """
    Invalidate the cache of a page, when it is updated/created/deleted
    """
    if raw:
        return
    build_page_key_index()


def section_cache_invalidator( sender, instance, signal, raw=False, *args, **kwargs ):
    """
    Invalidate all pages in a given section when a section is updated/d
    """
    if raw:
        return
    # Get all pages belonging to the section and that is not embedded
    # (the rendering of embedded pages is not affected by sections)
    qs = instance.page_set.filter( embedded__exact=0 )

    for p in qs:
        if p.embedded:
            cache.delete( CACHE_KEY['embedded_pages'] + str(p.pk) )
        else:
            for url in p.url_set.all():
                cache.delete( '%s_%s_internal' % (CACHE_KEY['pages'], str(url.url.__hash__())) )
                cache.delete( '%s_%s_external' % (CACHE_KEY['pages'], str(url.url.__hash__())) )


def generate_page_id(sender, instance, signal, raw=False, *args, **kwargs):
    """
    Generate a unique page ID
    """
    if raw or instance.id:
        return

    max_id = 0
    for pk in Page.objects.values_list('id', flat=True):
        try:
            pk = int(pk)
        except ValueError:
            # We're only intersted in string integers, skip!
            continue
        if pk > max_id:
            max_id = pk
    instance.id = str(max_id + 1)


# Listen for signals sent when Pages are updated/created/deleted
signals.post_save.connect( page_cache_invalidator, sender=Page )
signals.pre_delete.connect( page_cache_invalidator, sender=Page )
signals.post_save.connect( page_cache_invalidator, sender=PageProxy )
signals.pre_delete.connect( page_cache_invalidator, sender=PageProxy )
signals.post_save.connect( url_cache_invalidator, sender=URL )
signals.pre_delete.connect( url_cache_invalidator, sender=URL )
signals.post_save.connect( page_key_cache_invalidator, sender=EmbeddedPageKey )
signals.pre_delete.connect( page_key_cache_invalidator, sender=EmbeddedPageKey )
# Listen for signals sent when Sections are updated/created/deleted
signals.post_save.connect( section_cache_invalidator, sender=Section )
# Ensure that we start out with a URL index

# Signal to generate page ID on pre-save
signals.pre_save.connect( generate_page_id, sender=Page)
