"""test_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from djangoplicity.releases.models import Release
from djangoplicity.releases.options import ReleaseOptions
from djangoplicity.media.models import Image, Video, PictureOfTheWeek, ImageComparison
from djangoplicity.media.options import ImageOptions, VideoOptions, PictureOfTheWeekOptions, ImageComparisonOptions
from test_project.admin import admin_site, adminlogs_site


urlpatterns = [
    # Djangoplicity Administration
    url(r'^admin/', include(admin_site.urls), {'extra_context': {'ADMIN_SITE': True}}),
    url(r'^admin/cache/', include('djangoplicity.cache.urls', namespace="admincache_site", app_name="cache")),
    url(r'^admin/history/', include('djangoplicity.adminhistory.urls', namespace="adminhistory_site", app_name="history")),
    url(r'^admin/system/', include(adminlogs_site.urls), {'extra_context': {'ADMINLOGS_SITE': True}}),
    url(r'^admin/', include('djangoplicity.metadata.wtmlimport.urls'), {'extra_context': {'ADMIN_SITE': True}}),
    url(r'^admin/import/', include('djangoplicity.archives.importer.urls')),
    url(r'^tinymce/', include('tinymce.urls')),

    # Media Archive (Order of the URLs is important because they have common subpaths)
    url(r'^news/', include('djangoplicity.releases.urls'), {'model': Release, 'options': ReleaseOptions, 'translate': True}),
    url(r'^images/iotw/', include('djangoplicity.media.urls_potw'), {'model': PictureOfTheWeek, 'options': PictureOfTheWeekOptions, 'translate': True}),
    url(r'^images/comparisons/', include('djangoplicity.media.urls_imagecomparisons'), {'model': ImageComparison, 'options': ImageComparisonOptions, 'translate': True}),
    url(r'^images/', include('djangoplicity.media.urls_images'), {'model': Image, 'options': ImageOptions, 'translate': True}),
    url(r'^videos/', include('djangoplicity.media.urls_videos'), {'model': Video, 'options': VideoOptions, 'translate': True}),

    # Apps
    url(r'^reports/', include('djangoplicity.reports.urls')),
    url(r'^eventcalendar/', include('djangoplicity.eventcalendar.urls'))
    url( r'^facebook/', include('djangoplicity.iframe.urls')  ),
]

# This only works if DEBUG=True
if settings.SERVE_STATIC_MEDIA:
   from django.conf.urls.static import static
   urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
