Django Projects
===============


Applications
------------
NOTES: easy_installable, self-contained, tested, directory structure

**Directory Structure**

::
	src/
		djangoplicity_appname/
			fixtures/
				<appname>_tests.json
			management/
				commands/
					<cmdname>.py
			db/
				fields.py
			forms/
				fields.py
			templates/
				...
			__init__.py
			admin_urls.py
			admin.py
			cron.py
			models.py
			tests_urls.py
			tests.py
			views.py
			urls.py
	docs/
	CREDITS
	INSTALL
	LICENSE
	MANIFEST.in
	README
	setup.py

Project
-------

**Directory Structure**

::

	src/
		<prjname>/
			<app1>/
			<app2>/
			__init__.py
			manage.py
			forms.py
			pages.py
			settings.py
			urls.py
			views.py
	apps/
		Django-1.0.2-final.tar.gz
		...
	bin/
		install_<>.sh
	conf/
		crontab.txt
		settings-integration.ini
		settings-production.ini
		settings-<hostname1>.ini
		...
	docs/
		conf.py
		index.rst
		Makefile		
	fixtures/
		initial_data.json
	migration/
	static/
	templates/
		<appname>/
			...
		base.html
		base_twocolumn.html
		frontpage.html
		login.html
		logout.html
	fabfile.py
	pavement.py


Settings
--------

pavement.py
-----------

djangoplicity-paver

Install Scripts
---------------
- easy_install
- install scripts

fabfile.py
-----------

Admin Interfaces
----------------

In ``project/app/admin.py``::
	
	from django.contrib import admin
	from models import *
	
	class SomeModelAdmin( admin.ModelAdmin ):
		pass

	# 
	def register_with_admin( admin_site ):
		admin_site.register( SomeModel, SomeModelAdmin )
	
	register_with_admin( admin_site )

In ``project/admin.py``::

	
	from django.contrib.admin.sites import AdminSite
	from djangoplicity.contrib.admin.discover import autoregister

	# Import all admin interfaces needed
	import app.admin

	# Register each applications admin interfaces with
	# an admin site.
	admin_site = AdminSite()

	autoregister( admin_site, app.admin )


In ``projet/urls.py``::
	from project.admin import admin_site

	urlpatterns = ( '',
		( r'^admin/doc/', include( 'django.contrib.admindocs.urls' )),
		( r'^admin/(.*)', admin_site.root ),
	)