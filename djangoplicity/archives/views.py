# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>

from builtins import str
from builtins import object
from os.path import basename

from datetime import datetime

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist, \
    FieldDoesNotExist
from django.urls import NoReverseMatch
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.template import loader
from django.template.loader import render_to_string
from django.utils.encoding import force_unicode
from django.utils.http import urlunquote
from django.utils.translation import ugettext_lazy as _, ugettext
from django.views.generic import DetailView, ListView

from djangoplicity.archives import CACHE_PREFIX, _gen_cache_key
from djangoplicity.archives.queries import ArchiveQuery
from djangoplicity.archives.utils import is_internal, get_instance_checksum
from djangoplicity.archives.browsers import lang_templates, default_search_url

SEARCH_VAR = 'search'

# Get archive crosslinks from settings module if exists, default to empty dictionary
ARCHIVE_CROSSLINKS = settings.ARCHIVE_CROSSLINKS if hasattr(settings, 'ARCHIVE_CROSSLINKS') else {}


def _authorize_internal(request, kwargs):
    '''
    Check if the archive page is restricted to internal access only
    '''
    if 'internal' in kwargs and kwargs['internal']:
        # Check if InternalRequestMiddleware has already verified if the
        # client's IP was internal:
        try:
            internal = request.META['INTERNAL_REQUEST']
        except KeyError:
            internal = is_internal(request)

        if not internal:
            raise Http404


def _authorize_request( request, options, obj, published=None, next=None ):
    """
    Authorize the display of an archive page (based on published/not published) or redirect to login.
    """
    if next is None:
        next = request.get_full_path()

    staging_rights = options.has_staging_perms( request, obj )
    if not staging_rights:
        if request.user.is_authenticated():
            return HttpResponseForbidden(render_to_string('403.html', request=request))
        else:
            return redirect_to_login( next=next )

    return None


def _authorize_request_releasedate( request, options, obj, release_date=None, embargo_date=None, next=None ):
    """
    Authorize the display of an archive page or redirect to login.
    """
    now = datetime.now()

    if next is None:
        if hasattr(options, 'authorize_next_rewrite') and options.authorize_next_rewrite:
            next = request.build_absolute_uri()
            next = next.replace(*options.authorize_next_rewrite)
        else:
            next = request.get_full_path()

    if embargo_date:
        if embargo_date > now:
            staging_rights = options.has_staging_perms( request, obj )
            if not staging_rights:
                if request.user.is_authenticated():
                    return HttpResponseForbidden(render_to_string('403.html', request=request ))
                else:
                    return redirect_to_login( next=next )

    if release_date:
        if release_date > now:
            staging_rights = options.has_staging_perms( request, obj )
            embargo_rights = options.has_embargo_perms( request, obj )
            if not ( staging_rights or embargo_rights ):
                if request.user.is_authenticated():
                    return HttpResponseForbidden(render_to_string('403.html', request=request ))
                else:
                    return redirect_to_login( next=next )

    return None


def _process_object_group( obj, options, attr ):
    infoattr = getattr( options, attr, None )

    if infoattr is None:
        return None

    groups = []

    for group in infoattr:
        name = _(group[0])
        if 'links' in group[1]:
            links = []
            for l in group[1]["links"]:
                if callable(l):
                    url = l(obj)
                    if url:
                        links.append( { 'title': ugettext( getattr(l, 'short_description', l.__name__.replace('_', ' ').title() ) ), 'url': url } )
                else:
                    val = getattr( obj, l )
                    if callable(val):
                        fname = getattr( val, 'short_description', val.__name__ )
                        val = val()
                    else:
                        fname = obj._meta.get_field(l).verbose_name.title()
                    links.append( { 'title': _( fname ), 'url': val } )

        else:
            links = None
        if 'fields' in group[1]:
            metadata = []
            for f in group[1]["fields"]:
                if callable(f):
                    metadata.append( { 'field_name': _( getattr(f, 'short_description', f.__name__.replace('_', ' ').title()) ), 'field_value': f(obj)  } )
                else:
                    val = getattr( obj, f )
                    if callable(val):
                        fname = getattr( val, 'short_description', val.__name__ )
                        val = val()
                    else:
                        fname = obj._meta.get_field(f).verbose_name
                    metadata.append( { 'field_name': _( fname ), 'field_value': val } )
        else:
            metadata = None
        if 'category' in group[1]:
            category = []
            try:
                category = obj.archive_category.all()
                category = [{ 'name': e.name, 'fullname': e.fullname} for e in category]
            except Exception as e:
                pass
        else:
            category = None

        info = {
            'name': name,
            'links': links,
            'metadata': metadata,
            'category': category
        }

        groups.append(info)

    return groups


def process_object_info( obj, options ):
    """
    Determine object info to be displayed.
    """
    return _process_object_group( obj, options, 'info' )


def process_object_admin( obj, options ):
    """
    Determine object info to be displayed for users with admin
    rights.
    """
    return _process_object_group( obj, options, 'admin' )


def process_object_downloads( obj, options ):
    """ Determine downloads to display. """
    downloadattr = getattr( options, 'downloads', None )

    if downloadattr is None:
        return None

    groups = []

    for group in downloadattr:
        name = group[0]

        # Test if this section should be displayed
        if "condition" in group[1]:
            func_condition = group[1]["condition"]
            if callable(func_condition):
                if not func_condition( obj ):
                    continue
            elif func_condition:
                continue

        # Fetch icons
        if "icons" in group[1]:
            icons = group[1]["icons"]
        else:
            icons = {}

        # Thumbnail for group
        thumbnails = []
        if 'thumbnails' in group[1]:
            tnails = group[1]["thumbnails"]
            for tr, l in list(tnails.items()):
                resource_t = getattr( obj, '%s%s' % (obj.Archive.Meta.resource_fields_prefix, tr), False )
                if resource_t:
                    resource_l = getattr( obj, '%s%s' % (obj.Archive.Meta.resource_fields_prefix, l), False )
                    if resource_l:
                        thumb = (resource_t.url, resource_l.url)
                    else:
                        thumb = (resource_t.url, None)
                    thumbnails.append(thumb)

        # Look through resources
        if "resources" in group[1]:
            resources = group[1]["resources"]

            downloads = []

            for rname in resources:
                # A resource can be both a name of a resource
                # in the model or a function that returns link
                # and size.
                if callable( rname ):
                    keyname = rname.__name__
                else:
                    keyname = rname

                if keyname in icons:
                    icon = icons[keyname]
                else:
                    icon = None

                if callable( rname ):
                    attrs = rname( obj )
                    if attrs is not None:
                        attrs['icon'] = icon or 'default'
                        try:
                            attrs['title'] = rname.short_description
                        except:
                            attrs['title'] = rname.__name__.replace('_', ' ').title()
                        downloads.append( attrs )
                else:
                    m = getattr( obj.Archive, rname, False )
                    r = getattr( obj, '%s%s' % (obj.Archive.Meta.resource_fields_prefix, rname), False )

                    if m and r:
                        try:
                            downloads.append({
                                'name': m.name,
                                'title': m.verbose_name,
                                'url': r.url,
                                'size': r.size,
                                'icon': icon or 'default',
                                'extra_attrs': '',
                                'checksum': get_instance_checksum(obj, rname),
                                'filename': basename(r.name) if r.name else '',
                            })
                        except IOError:
                            # File is not readable, we exclude it from the list
                            continue
        else:
            downloads = None

        download = {
            'name': name,
            'downloads': downloads,
            'thumbnails': thumbnails,
        }

        groups.append(download)

    return groups


class GenericDetailView( object ):
    def __init__(self ):
        """ """

    options = None

    cache_key_prefix = CACHE_PREFIX['detail_view']

    def vary_on(self, request, model, obj, state, admin_rights, **kwargs ):
        """
        Determine the specific version of page being generated, so that
        we can properly cache the page.

        If a view can generate more than one page, this function
        must return a list of strings on the parameters it can vary on.
        An empty list is the default page.
        """

        return ['internal'] if request.META.get( 'INTERNAL_REQUEST', False ) else []

    def response(self, html, **kwargs ):
        """ Generate the HttpReposnse """
        return HttpResponse( html, content_type=self.options.content_type )

    def select_template( self, model, obj, suffix="" ):
        """
        Select the template to used for rendering
        """
        template_names = []

        # Use detail template specified in a field in the instance if available
        if self.options.template_name_field:
            template_names.append( getattr( obj, self.options.template_name_field ) )

        # Use detail template specified in ArchiveOptions object if specified
        if self.options.template_name:
            template_names.append( self.options.template_name )

        # Use default detail templates
        template_names.append( "archives/%s/detail%s.html" % ( model._meta.object_name.lower(), suffix ) )
        template_names.append( "archives/detail%s.html" % suffix )

        if settings.USE_I18N:
            template_names = lang_templates( model, template_names ) + template_names

        return loader.select_template( template_names )

    def render( self, request, model, obj, state, admin_rights, **kwargs ):
        """
        Render the detail page for the object taking into account
        the current state and admin rights.
        """
        #
        # Extra context setup
        #
        extra_context = self.options.extra_context( obj )
        if extra_context is None:
            extra_context = {}
        extra_context.update( state )

        #
        # Select template
        #
        t = self.select_template( model, obj )

        #
        # Search URL
        #
        searchable = False
        search_url = ''

        try:
            search_url = default_search_url( self.options )
            searchable = True if search_url else False
        except NoReverseMatch:
            pass

        # Cross links
        crls = ARCHIVE_CROSSLINKS.get(self.options.urlname_prefix, ())
        crosslinks_subject = model._meta.verbose_name_plural

        crosslinks = []
        for website, url in crls:
            str = _('%(products)s on %(website)s') % {'products': force_unicode(crosslinks_subject), 'website': website}
            crosslinks.append((str, url))

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
        # Request context setup
        #
        context = {
            'object': obj,
            'resources_template': self.options.resources_template,
            'info_template': self.options.info_template,
            'admin_template': self.options.admin_template,
            'description_template': self.options.description_template,
            'archive': model._meta.verbose_name,
            'archive_title': self.options.title,
            'info_groups': process_object_info( obj, self.options ),
            'resources_groups': process_object_downloads( obj, self.options ),
            'admin_groups': process_object_admin( obj, self.options ) if admin_rights else None,
            'searchable': searchable,
            'search_url': search_url or '',
            'search_specific': model._meta.verbose_name_plural,
            'crosslinks': crosslinks,
            'crosslinks_subject': crosslinks_subject,
            'right_column_page': right_column_page,
        }

        #
        # Process callables in extra context
        #
        for k, value in list(extra_context.items()):
            if callable(value):
                context[k] = value()
            else:
                context[k] = value

        return t.render(context, request)


class SerializationDetailView( GenericDetailView ):
    """
    Serialization view - will serialize the object into a machine readable form.
    """
    def __init__( self, serializer=None, emitters=None, allowed_ips=None, allowed_hosts=None ):
        if emitters is None:
            emitters = []
        super(SerializationDetailView, self).__init__()
        self.serializer = serializer()
        self._mapping = {}
        for e in emitters:
            self._mapping[e.name] = e

        self.allowed_ips = allowed_ips
        self.allowed_hosts = allowed_hosts

    def vary_on(self, request, model, obj, state, admin_rights, serializer='json', **kwargs ):
        return ['serialization', serializer]

    def render( self, request, model, obj, state, admin_rights, serializer='json', **kwargs ):
        if serializer.lower() not in self._mapping:
            raise Http404

        # Allow only ESO into the web service
        if self.allowed_ips or self.allowed_hosts:
            allow = False
            if 'HTTP_X_REAL_IP' in request.META:
                remotehost = request.META['HTTP_X_REAL_IP']
            else:
                remotehost = request.META['REMOTE_ADDR']
            for h in self.allowed_ips:
                if remotehost.startswith( h ):
                    allow = True
            for h in self.allowed_hosts:
                if remotehost.endswith( h ):
                    allow = True

            if not allow:
                raise Http404

        # if not isinstance( obj, Serializable ):
        #   raise Exception("Object is not serializable")

        emitter = self._mapping[serializer.lower()]()
        return emitter.emit(  self.serializer.serialize( obj ) )

    def response( self, data, serializer='json', **kwargs ):
        response = HttpResponse( data, content_type=self._mapping[serializer.lower()].content_type )
        return response


def archive_detail( request, object_id=None, slug=None, model=None, options=None, detail_view=None, **kwargs ):
    """
    Generic detail view for browsing and archive - based on generic object_detail view
    but extended to take publishing
    """
    #
    # Pre-flight checks
    #

    # Check if the view is restricted to internal access:
    _authorize_internal(request, kwargs)

    if not isinstance( detail_view, GenericDetailView ):
        raise ImproperlyConfigured("Generic archive detail view must be installed rendering class.")

    if options is None or model is None:
        raise ImproperlyConfigured("Generic archive detail view must be installed in the URL conf with model and options field.")

    #
    # Get object either from cache or from database
    #
    if object_id:
        key = _gen_cache_key( detail_view.cache_key_prefix, model.__name__, object_id )
    elif slug and options.slug_field:
        key = _gen_cache_key( detail_view.cache_key_prefix, model.__name__, slug )
    else:
        raise AttributeError("Generic archive detail view must be called with either an object_id or a slug/slug_field.")

    try:
        ca = cache.get(key)

        if ca:
            obj = ca['obj']
        else:
            queryset = options.detail_queryset( model )

            if options.select_related:
                queryset = queryset.select_related(*options.select_related)

            if options.prefetch_related:
                queryset = queryset.prefetch_related(*options.prefetch_related)

            # Determine queryset by using object_id or pk as ID field.
            if object_id:
                filterkwargs = { 'pk': object_id }
            elif slug and options.slug_field:
                filterkwargs = {options.slug_field: slug}

            obj = queryset.filter( **filterkwargs ).get()
    except ObjectDoesNotExist:
        # Check if we have a similar object in the default language
        obj = options.detail_notfound( model, **filterkwargs )
        if not obj:
            raise Http404("No %s found matching the query" % (model._meta.verbose_name))
        elif request.PREFERRED_LANGUAGE and obj.lang and request.PREFERRED_LANGUAGE[:2] == obj.lang[:2]:
            # We don't have the exact language, but we do have one from the
            # same family
            request.NO_TRANSLATION = False
        else:
            # We set a variable to be used in the template to indicate
            # that the object is not in the current language
            request.NO_TRANSLATION = True
    #
    # Embargo staging functionality
    #
    state = { 'is_embargo': False, 'is_staging': False, 'is_published': True }
    now = datetime.now()

    # Test if item is published or not.
    if model.Archive.Meta.published:
        state['is_published'] = getattr( obj, model.Archive.Meta.published_fieldname, None )

        # Only authorize request if actually needed.
        if not state['is_published']:
            view = _authorize_request( request, options, obj )
            if view:
                return view

    # Test if item is release, embargoed or staging
    if model.Archive.Meta.release_date or model.Archive.Meta.embargo_date:
        # For release dates in the model itself.
        release_date = getattr( obj, model.Archive.Meta.release_date_fieldname, None )
        embargo_date = getattr( obj, model.Archive.Meta.embargo_date_fieldname, None )
        view = _authorize_request_releasedate( request, options, obj, release_date, embargo_date )
        if view:
            return view
        if model.Archive.Meta.release_date and release_date:
            state['is_embargo'] = release_date > now
        if model.Archive.Meta.embargo_date and embargo_date:
            state['is_staging'] = embargo_date > now
    elif hasattr(model.Archive.Meta, 'related_release_date') and hasattr(model.Archive.Meta, 'related_embargo_date'):
        if model.Archive.Meta.related_release_date or model.Archive.Meta.related_embargo_date:
            # For release dates in related models.
            rel_field = model.Archive.Meta.related_release_date[0]
            rel_model_field = model.Archive.Meta.related_release_date[1]
            emb_field = model.Archive.Meta.related_embargo_date[0]
            emb_model_field = model.Archive.Meta.related_embargo_date[1]
            release_date = getattr( getattr( obj, rel_field, None ), rel_model_field, None )
            embargo_date = getattr( getattr( obj, emb_field, None ), emb_model_field, None )
            view = _authorize_request_releasedate( request, options, obj, release_date, embargo_date )
            if view:
                return view
            if model.Archive.Meta.related_release_date and release_date:
                state['is_embargo'] = release_date > now
            if model.Archive.Meta.related_embargo_date and embargo_date:
                state['is_staging'] = embargo_date > now

    #
    # Admin rights functionality
    #

    # Delegate to options object to determine if request has
    # access to object.
    ( admin_rights, vary_on_params ) = options.has_admin_perms( request, obj )

    #
    # Cache vary on parameter
    #
    vary_on_params.extend( detail_view.vary_on( request, model, obj, state, admin_rights, **kwargs ) )

    # Generate a key for the specific combination of
    # parameters that a page can have
    htmlkey = "html"
    if vary_on_params:
        htmlkey = "%s_%s" % ( htmlkey, "_".join( vary_on_params ) )

    # Cache validation - is stored cache dirty (e.g. it's displaying embargo
    # even though it's no longer embargoed)
    is_dirty = (ca is not None and ca['state'] != state)

    # ====================================
    #
    # Rendering
    #
    if ca is not None and (not is_dirty) and htmlkey in ca:
        # Cached page exists
        html = ca[htmlkey]
    else:
        #
        # Render template
        #
        html = detail_view.render( request, model, obj, state, admin_rights, **kwargs )

        #
        # Save in cache
        #
        if ca is None:
            # No previous cache exists, so create new.
            cache.set( key, {'obj': obj, htmlkey: html, 'state': state} )
        else:
            # Previous cache exists, so only set the missing html key.
            ca[htmlkey] = html
            cache.set( key, ca )

    # Return response (either cached or just rendered)
    response = detail_view.response( html, **kwargs )
    return response


def archive_list( request, model=None, options=None, query_name=None, query=None, page=1, viewmode_name=None, **kwargs ):
    """
    List view for archives
    """

    # Check if the view is restricted to internal access:
    _authorize_internal(request, kwargs)

    #
    # Initial error checking - make sure we have a query
    #

    # options and model classes required
    if options is None or model is None:
        raise ImproperlyConfigured("Generic archive list view must be installed in the URL conf with model and options parameters.")

    # query name or a query required
    if not ( query_name or query ):
        raise Http404

    if query_name:
        query = getattr( options.Queries, query_name, None )

    if not ( query is not None and isinstance( query, ArchiveQuery ) ):
        raise Http404

    # Check if request is internal and generate cache key
    if is_internal(request):
        key = '%s_archive_list_internal_%s' % (model.get_cache_key_prefix(), str(request.path.__hash__()))
    else:
        key = '%s_archive_list_external_%s' % (model.get_cache_key_prefix(), str(request.path.__hash__()))

    #
    # Determine archive browser
    #
    if viewmode_name is None:
        if query.viewmode_param is not None:
            viewmode_name = request.GET.get( query.viewmode_param, query.default_browser )
        else:
            viewmode_name = query.default_browser

    if not query.has_browser( viewmode_name ):
        raise Http404

    try:
        browser = getattr( options.Browsers, viewmode_name )
    except AttributeError:
        raise Http404

    # Check if view in cache:
    ca = model.cache_get( key )

    #
    # Authorize view
    #
    if not query.has_permissions( request ):
        if request.user.is_authenticated():
            return HttpResponseForbidden(render_to_string('403.html', request=request ))
        else:
            return redirect_to_login( next=request.get_full_path() )

    # Check parameters and redirect if necessary:
    redirect_url = query.check_parameters(model, options, request)
    if redirect_url:
        return redirect(redirect_url)

    # We don't used cached view if we have GET data (to prevent
    # caching search queries)
    if ca and not request.GET:
        return browser.response( ca )

    #
    # Get Query Set
    #
    (qs, query_data) = query.queryset(model, options, request, **kwargs)

    # Exclude all non-published archive items (if archive uses published attribute)
    # FIXME: this results in duplicates "published=1" in the SQL. Really this
    # should be done in the query, like in AllPublicQuery, however some queries
    # such as SubjectCategoryNamePublicQuery need to be updated (SubjectCategoryNameQuery should for example
    # inherit from AllPublicQuery instead of SubjectCategoryNameQuery)
    if model.Archive.Meta.published:
        if hasattr(qs, 'filter'):
            qs = qs.filter( **{ model.Archive.Meta.published_fieldname: True } )

    if options.select_related:
        qs = qs.select_related(*options.select_related)

    if options.prefetch_related:
        qs = qs.prefetch_related(*options.prefetch_related)

    if options.archive_list_only_fields:
        qs = qs.only(*options.archive_list_only_fields)

    #
    # Search in query set if query is searchable.
    #
    search_str = request.GET.get( SEARCH_VAR, '' ).strip()
    search_str = query_data.get('adv_search_str', search_str)

    if search_str and '\0' in urlunquote(search_str):
        # Tell Nginx to drop connection if someone is passing null bytes
        # to the query
        return HttpResponse(status=444)

    if query.searchable and search_str and not query_data.get('adv_search_str', False):
        qs = options.search(request, qs, search_str)

    #
    # Render results
    #
    kwargs.update( { 'page': page, 'viewmode_name': viewmode_name } )  # Temp hack
    content = browser.render( request, model, options, query, query_name, qs, query_data, search_str, **kwargs )

    if not request.GET:
        model.cache_set( key, content )

    return browser.response( content )


class BaseDetailView(DetailView):
    '''
    Extends on Django's DetailView and updates the context and queryset
    to filter out published, etc.
    TODO: handle embargo
    '''
    def get_context_data(self, **kwargs):
        ctx = super(BaseDetailView, self).get_context_data(**kwargs)

        # Check if item is published and user has permissions
        published = getattr(self.object, 'published', True)
        if not published and not self.request.user.has_perms('change_post'):
            raise Http404

        # Check if the item has a release date in the future
        embargo = False
        if hasattr(self.object, 'release_date') and \
            datetime.now() < self.object.release_date:
            embargo = True
            if not self.request.user.has_perms('change_post'):
                raise Http404

        ctx['is_published'] = published
        ctx['is_embargo'] = embargo

        return ctx


class BaseListView(ListView):
    paginate_by = 10

    def get_queryset(self):
        qs = super(BaseListView, self).get_queryset()

        def has_field(model, field):
            try:
                if model._meta.get_field(field):
                    return True
            except FieldDoesNotExist:
                return False

        # Filter unpublished items if supported
        if has_field(self.model, 'published'):
            qs = qs.filter(published=True)

        # Filter by release date if supported
        if has_field(self.model, 'release_date'):
            qs = qs.filter(release_date__lte=datetime.now())

        return qs
