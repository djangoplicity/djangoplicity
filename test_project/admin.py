from djangoplicity.contrib.admin.sites import AdminSite
from djangoplicity.contrib.admin.discover import autoregister

# Import all admin interfaces we need
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.sites.models import Site
from django.contrib.sites.admin import SiteAdmin
from django.contrib.redirects.models import Redirect
from django.contrib.redirects.admin import RedirectAdmin
from djangoplicity.reports import admin as reports_admin
# import djangoplicity.archives.contrib.satchmo.freeorder.admin

import importlib

# Register each applications admin interfaces with
# an admin site.
from djangoplicity.metadata.admin import CategoryTypeAdmin
from djangoplicity.metadata.models import CategoryType

admin_site = AdminSite(name="admin_site")
adminlogs_site = AdminSite(name="adminlogs_site")
adminshop_site = AdminSite(name="adminshop_site")

admin_sites_modules_config = [
    {
        'site': admin_site,
        'modules': [
            'django.contrib.auth.admin',
            'django.contrib.sites.admin',
            'djangoplicity.menus.admin',
            'djangoplicity.pages.admin',
            'djangoplicity.metadata.admin',
            'djangoplicity.announcements.admin',
            'djangoplicity.media.admin',
            'djangoplicity.releases.admin',
            # 'djangoplicity.products.admin',
            # 'djangoplicity.science.admin',
            # 'djangoplicity.mailinglists.admin',
            # 'djangoplicity.newsletters.admin',
            # 'djangoplicity.customsearch.admin',
            # 'djangoplicity.contacts.admin',
            # 'djangoplicity.eventcalendar.admin',
            # 'djangoplicity.events.admin',
        ],
    },
    {
        'site': adminlogs_site,
        'modules': [
            # 'djangoplicity.actions.admin'
        ]
    }
]

for site_config in admin_sites_modules_config:
    for module_name in site_config['modules']:
        # Auto import admin module
        admin_module = importlib.import_module(module_name)
        # Then register the imported module to the respective admin_site using the custom config
        autoregister(site_config['site'], admin_module)

# Applications that does not support above method.
admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)
admin_site.register(CategoryType, CategoryTypeAdmin)
reports_admin.advanced_register_with_admin(admin_site)

adminlogs_site.register(Site, SiteAdmin)
adminlogs_site.register(Redirect, RedirectAdmin)

# ADMIN SHOP SITE MODULES
# from djangoplicity.archives.contrib.satchmo.admin import satchmo_admin
# adminshop_site = satchmo_admin(adminshop_site)
# autoregister(adminshop_site, djangoplicity.archives.contrib.satchmo.freeorder.admin)
