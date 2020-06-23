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
from django.conf.urls import url, include
from django.contrib import admin
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

    # Apps
    url(r'^reports/', include('djangoplicity.reports.urls')),
]
