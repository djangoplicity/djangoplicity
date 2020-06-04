from django.contrib.admin.sites import AdminSite as DjangoAdminSite
from functools import update_wrapper


class AdminSite( DjangoAdminSite ):
    """
    Subclass of Django admin site to ensure that extra_context variable can
    be passed to the templates.

    Usage (in code)::

      # from django.contrib.admin.sites import AdminSite <-- old line, which is replaced with the next line.
      from djangoplicity.contrib.admin.sites import AdminSite
      admin_site = AdminSite( name="admin_site" )
      admin_site.register( ... )

    Above will allow you to include extra_context in the view parameters::

      ( r'^/admin/', include( admin_site.urls ), { 'extra_context' : ... } ),
    """

    EXTRA_CONTEXT_VIEWS = [
        "django.contrib.admin.sites.index",
        "djangoplicity.contrib.admin.sites.index",
        "django.contrib.admin.sites.app_index",
        "djangoplicity.contrib.admin.sites.app_index",
    ]

    def has_extra_context( self, view ):
        """
        Determine if view can take extra_context
        """
        viewname = "%s.%s" % ( view.__module__, view.__name__ )
        return viewname in self.EXTRA_CONTEXT_VIEWS

    def admin_view( self, view, cacheable=False ):
        """
        Ensure extra_context is only provided to views that can handle it.
        """
        view = super( AdminSite, self ).admin_view( view, cacheable=cacheable )

        if not self.has_extra_context( view ):
            def inner( *args, **kwargs ):
                if 'extra_context' in kwargs:
                    del kwargs['extra_context']
                return view( *args, **kwargs )

            return update_wrapper( inner, view )
        else:
            return view

    def get_urls(self):
        """
        Hack to make logout take extra_context - apparently, it's not enough to override the function.
        """
        from django.conf.urls import url
        from django.contrib.contenttypes.views import shortcut
        urlpatterns = [url(r'^r/(?P<content_type_id>\d+)/(?P<object_id>.+)/$', self.admin_view(shortcut))]
        urlpatterns += super( AdminSite, self ).get_urls()
        return urlpatterns
