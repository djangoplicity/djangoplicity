# coding: utf-8
#
# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>

from builtins import object
import os

from django.conf import settings
from django.core.paginator import InvalidPage
from django.urls import reverse, NoReverseMatch
from django.http import Http404, HttpResponse
from django.template import loader, TemplateDoesNotExist
from django.utils.encoding import force_text
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _

from djangoplicity.archives.queries import urlname_for_query
from djangoplicity.utils.pagination import DjangoplicityPaginator

__all__ = ( 'ArchiveBrowser', )

if settings.USE_I18N:
    from django.utils import translation
    from djangoplicity.translation.models import TranslationModel, translation_reverse
    reverse_func = translation_reverse

    def reverse_kwargs():
        return {'lang': translation.get_language()}

    def vary_on_lang():
        return [translation.get_language(), ]
else:
    reverse_func = reverse

    def reverse_kwargs():
        return {}

    def vary_on_lang():
        return []


def default_search_url( options ):
    """
    Obtain the URL to the default search query.
    """
    default_query = options.default_query()

    if default_query and default_query.searchable:
        try:
            default_q_name = options.Queries.Meta.default
        except AttributeError:
            default_q_name = 'default'

        return reverse_func( urlname_for_query( options, default_query, default_q_name, False ), **reverse_kwargs() )
    else:
        return ''


def lang_templates( model, template_names ):
    """
    Takes a list of template names and generate language specific names for them.
    """
    if issubclass( model, TranslationModel ):
        lng = translation.get_language()
        lang_template_names = []

        for tpl in template_names:
            ( base, ext ) = os.path.splitext( tpl )
            lang_template_names.append( "%s.%s%s" % ( base, lng, ext ) )

        return lang_template_names
    return []


def lang():
    if settings.USE_I18N:
        return translation.get_language()
    else:
        return None


def select_template( template_names ):
    for name in template_names:
        try:
            loader.get_template( name )
            return name
        except TemplateDoesNotExist:
            continue
    return None


class ArchiveBrowser( object ):
    """
    ArchiveBrowser are responsible for rendering the list part of a page which includes
    - listing all items
    - rendering paginator
    - rendering status bar

    The ArchiveBrowser is however not responsible for choosing the main template to be rendered.
    This is done by an ArchiveQuery.
    """

    def __init__( self, verbose_name=None, paginate_by=None, index_template=None, allow_empty=None, template_name=None, extra_context=None, content_type=None, display=True ):
        """
            verbose_name -
            paginate_by -
            allow_empty -
            extra_context - A dictionary of values to add to the template context. By default, this
                            is an empty dictionary. If a value in the dictionary is callable, the
                            generic view will call it just before rendering the template.
            mimetype -    The MIME type to use for the resulting document. Defaults to the value
                            of the DEFAULT_CONTENT_TYPE setting.
        """
        self.verbose_name = verbose_name or _( 'Default view mode' )
        self._paginate_by = paginate_by or settings.DEFAULT_PAGINATE_BY
        self.allow_empty = allow_empty or True
        self.template_name = template_name
        self.index_template = index_template
        self.extra_context = extra_context
        self.content_type = content_type
        self.display = True

    def paginate_by( self, request ):
        return self._paginate_by

    def pagination( self, options, qs, request, page=1 ):
        #
        # Get data and paginator
        #
        paginator = DjangoplicityPaginator( qs, per_page=self.paginate_by( request ), allow_empty_first_page=self.allow_empty )

        # Determine page to view
        try:
            page_number = int( page )
        except TypeError:
            page_number = 1
        except ValueError:
            if page == 'last':
                page_number = paginator.num_pages
            else:
                # Page is not 'last', nor can it be converted to an int.
                raise Http404

        # Evaluate query set - i.e. get the actual data.
        try:
            page_obj = paginator.page( page_number )
            options.process_object_list( page_obj.object_list )
        except InvalidPage:
            raise Http404

        return ( paginator, page_number, page_obj )

    def response( self, content, **kwargs ):
        """ Generate the HttpReposnse """
        return HttpResponse( content, content_type=self.content_type )

    def render( self, request, model, options, query, query_name, qs, query_data, search_str, **kwargs ):
        """
        Render the list view page for the objects.
        """
        #
        # Get Options
        #
        template_loader = loader
        extra_context = self.extra_context or {}
        index_template = self.index_template

        #
        # Pagination (will evaluate query set)
        #
        try:
            ( paginator, _page_number, page_obj ) = self.pagination( options, qs, request, page=kwargs['page'] )
        except KeyError:
            raise Http404

        # Arguments needed for reverse URL lookup
        query_args = query.url_args( model, options, request, **kwargs )

        # Determine view name and paginator url
        args = []
        args.extend( query_args )

        viewmode_name = kwargs['viewmode_name']

        if query.default_browser == viewmode_name:
            urlname = urlname_for_query( options, query, query_name, False )
        else:
            urlname = urlname_for_query( options, query, query_name, True )
            args.extend( [viewmode_name] )

        try:
            paginator_url = reverse_func( urlname, args=args, **reverse_kwargs() )
        except NoReverseMatch:
            paginator_url = ''

        #
        # Determine browsers
        #
        available_browsers = []
        current_browser = None
        for bname in query.browsers:
            if viewmode_name != bname:
                b = getattr( options.Browsers, bname )

                if b.display:
                    args = []
                    args.extend( query_args )

                    if query.default_browser == bname:
                        urlname = urlname_for_query( options, query, query_name, False )
                    else:
                        urlname = urlname_for_query( options, query, query_name, True )
                        args.extend( [bname] )

                    try:
                        url = reverse_func( urlname, args=args, **reverse_kwargs() )
                    except NoReverseMatch:
                        url = ''

            else:
                current_browser = bname

        #
        # Select template
        #

        # Index template
        index_template_names = [
                "archives/%s/%s" % ( model._meta.object_name.lower(), self.index_template ),
                "archives/%s" % self.index_template,
            ]

        index_template = select_template( index_template_names )

        # List template
        template_names = []

        # Browser-specific templates
        if current_browser:
            template_names.append( "archives/%s/list_%s.html" % ( model._meta.object_name.lower(), current_browser ) )

        if isinstance( query.extra_templates, list ):
            template_names.extend( query.extra_templates )
        elif callable( query.extra_templates ):
            template_names.extend( query.extra_templates( model, query, query_name, query_data ) )

        # Use default list templates
        template_names.append( "archives/%s/list.html" % ( model._meta.object_name.lower() ) )
        template_names.append( "archives/list.html" )

        # Internationalization for template I18N
        if settings.USE_I18N:
            template_names = lang_templates( model, template_names ) + template_names

        #
        # Determine feed URL for this specific query (if exists)
        #
        feed_urls = None
        listview_feed_url = None

        if hasattr( options, 'feeds' ):
            feeds = options.feeds()

            if not query.feed_name:
                query.feed_name = 'default'
            try:
                f = feeds[query.feed_name if query.feed_name != 'default' else '']
                listview_feed_url = f.archive_feed_url( name=query.feed_name, lang=lang(), reverse_func=reverse_func, **kwargs )
            except ( KeyError, AttributeError ):
                pass

        #
        # Search setup
        #
        searchable = False
        search_url = ''
        paginator_params = ''

        try:
            if query.searchable:
                search_url = reverse_func( urlname_for_query( options, query, query_name, False ), args=query_args, **reverse_kwargs() )
                searchable = True
            else:
                if query.search_default:
                    search_url = default_search_url( options )
                    searchable = True if search_url else False

            if search_str:
                paginator_params = urlencode( [( 'search', search_str )] )

                for b in available_browsers:
                    b['params'] = paginator_params

            if query_data.get( 'adv_search_str', False ):
                paginator_params = search_str
                for b in available_browsers:
                    b['params'] = paginator_params

        except NoReverseMatch:
            pass

        #
        # Preserve sort order
        #

        # save params without sorting information, for use in sorting buttons
        params_nosort = paginator_params

        # add sorting information
        params_nosearch = ''
        if 'sort' in request.GET:
            params_nosearch = urlencode( [( 'sort', request.GET['sort'] )] )
            if paginator_params:
                paginator_params += '&' + params_nosearch
            else:
                paginator_params = params_nosearch

        #
        # Cross links
        #
        ARCHIVE_CROSSLINKS = settings.ARCHIVE_CROSSLINKS if hasattr( settings, 'ARCHIVE_CROSSLINKS' ) else {}
        crls = ARCHIVE_CROSSLINKS.get( options.urlname_prefix, () )
        crosslinks_subject = model._meta.verbose_name_plural

        crosslinks = []
        crosslinks_string = _( 'Also see our %(products)s on ' ) % {'products': force_text( crosslinks_subject ).lower() }
        for website, url in crls:
            str = _('%(products)s on %(website)s') % {'products': force_text(crosslinks_subject), 'website': website}
            crosslinks.append( ( str, url ) )
            crosslinks_string += ( '<a href="%(url)s">%(website)s</a>, ' % {'website': website, 'url': url } )

        # empty string if no crosslinks
        if not len( crls ):
            crosslinks_string = ''
        # remove ', ' and add .
        else:
            crosslinks_string = crosslinks_string[:-2] + '.'

        #
        # Embedded page
        #
        try:
            from djangoplicity.pages.views import embed_page_key, PageNotFoundError
            right_column_page = embed_page_key( request, 'djangoplicity.archives.%s.right_column' % model._meta.object_name.lower() )
        except PageNotFoundError:
            right_column_page = ""
        except:
            right_column_page = ""

        #
        # Web Categories
        #
        from djangoplicity.metadata.models import Category
        category_type = options.urlname_prefix.capitalize()  # urlname_prefix is either 'images' or 'videos'
        web_categories = Category.objects.filter(type__name=category_type, enabled=True).select_related('type')
        selected_web_category = kwargs.get('stringparam', None)
        for x in web_categories:
            if x.url == selected_web_category:
                x.selected = True

        #
        # Programs
        #
        from djangoplicity.metadata.models import Program
        category_type = options.urlname_prefix.capitalize()  # urlname_prefix is either 'releases'
        programs = Program.objects.filter(type__name=category_type, enabled=True).select_related('type')
        selected_web_program = kwargs.get('stringparam', None)
        for x in programs:
            if x.url == selected_web_program:
                x.selected = True

        #
        # Request context setup
        #
        context = {
            'archive': model._meta.verbose_name,
            'archive_title': query.verbose_name( **query_data ),
            'archive_opengraph_image': options.opengraph_image,
            'index_template': index_template,
            'object_list': page_obj.object_list,
            'paginator': paginator,
            'paginator_prefix': settings.ARCHIVE_PAGINATOR_PREFIX,
            'paginator_url': paginator_url,
            'paginator_params': paginator_params,
            'params_nosort': params_nosort,
            'params_nosearch': params_nosearch,
            'feed_urls': feed_urls,
            'listview_feed_url': listview_feed_url,
            'page_obj': page_obj,
            'browsers': available_browsers,
            'searchable': searchable,
            'search_str': search_str or '',
            'search_str_verbose': query_data.get('search_str_verbose', ''),
            'search_url': search_url or '',
            'search_specific': model._meta.verbose_name_plural,
            'crosslinks': crosslinks,
            'crosslinks_string': crosslinks_string,
            'crosslinks_subject': crosslinks_subject,
            'right_column_page': right_column_page,
            'web_categories': web_categories,
            'programs': programs,
        }

        #
        # Process callables in extra_context
        #
        for key, value in list(extra_context.items()):
            if callable( value ):
                context[key] = value()
            else:
                context[key] = value

        t = template_loader.select_template( template_names )

        return t.render( context, request )
