Coding Guidelines for Django Projects 
=====================================

External Libraries
------------------

It is easy to make dependencies on external libraries, as well as internal modules. It is however very hard to get rid of them afterwards, hence care should be taken when creating dependencies.

**Licenses**

 * *DO NOT INCLUDE EXTERNAL CODE UNLESS YOU KNOW THE LICENSE AND COPYRIGHT HOLDER!*
 * Keep track of licenses, copyright holders and where source code was obtained for all external source code.
 * Proprietary libraries should only be included into projects that are not going to be public released.
 * MIT/BSD like open source licenses should used - GPL is too restrictive and affects not only the included library but also our code.

**Stability**
 * 


URLs
----
With respect to URLs there are some considerations and best practices to take into account.

**Human readable URLs**

Human readable URLs are an important part of a website seen from the users perspective, thus care should be take to craft logical/meaningful URLs for all django applications.

Examples::

	/resources/books/
	/resources/books/page/15/
	/resources/books/viewall/
	/resources/books/viewall/page/15/
	/resources/books/detail/book_eyes/

**Stable URLs** 

Never change existing URLs unless you have a good very reason. Changing URLs for the same resources can affect e.g. search engine ranking and external links to your site. Make sure to provide redirects. 

**Logical structure** 

The URLs should reflect a logical view of your site, that helps users identify where they are. 

**Pagination**

URLs for pagination should use the following scheme:
	* First page accessible at ``<prefix>/`` and ``<prefix>/page/1/``.
	* Subsequent pages accessible at ``<prefix>/page/<no>/``.
	
**Named URL-patterns**

To ensure that code/URLs as easy maintainable and reusable as possible, named URL-patterns should be used to a large extend to allow reverse URL matching. The problem occurs e.g. if the same view is used in two different URL patterns (happens often with e.g. pagination) - then the URL resolver does not know which to choose.

Following example show how to name a pattern and do a reverse lookup in either Python code or templates::

	# urls.py
	urlpatterns = patterns('',
	    url(r'^archive/(\d{4})/$', views.archive, name="full-archive" ),
		# ...
	)

	# in views.py
	from django.core.urlresolvers import reverse
	reverse( 'full-archive', args=[1945] )

	# in template.html
	{% url 'full-archive' 1945 %}
	

**References:**

 * http://docs.djangoproject.com/en/dev/topics/http/urls/


Internationalization & Unicode
------------------------------
All strings should be unicode strings and translated, unless there is a  (very) good reason (e.g. URLs which cannot use Unicode strings).

**Example:**
::
  from django.utils.translation import ugettext as _

  _( u'String to be translated') # Translated unicode string


**References:**

 * http://docs.djangoproject.com/en/dev/topics/i18n/
 * http://docs.djangoproject.com/en/dev/ref/unicode/

Documentation Style
-------------------
fab publish_docs

http://sphinx.pocoo.org/rest.html
http://sphinx.pocoo.org/markup/para.html

Markup constructs
^^^^^^^^^^^^^^^^^

* `.. note::`
* `.. warning::`
* `.. versionadded::`
* `.. versionchanged::`
* `.. centered::`
* `.. glossary::`
* `.. versionchanged::`
* `.. versionchanged::`



Source Code Formatting
----------------------

**File Header**

All source code files should start with a header like this::

	# -*- coding: utf-8 -*-
	#
	# <Project name>
	# Copyright <Year> <Copyright Holders>
	#
	# Authors:
	#   <Name> <<email>>
	#   <Name> <<email>>
	#

e.g.::

	# -*- coding: utf-8 -*-
	#
	# Djangoplicity
	# Copyright 2007-2009 ESO, ESA/Hubble
	#
	# Authors:
	#   Lars Holm Nielsen <lnielsen@eso.org>
	#   Luis Clara Gomes <lcgomes@eso.org>
	#

Note additionally, if the source code is going to be released, the header should also contain a **license** (MIT and BSD licenses are preferred for open source projects).

**Python Code**

 * Indention:
    * Use tabs
 * File encoding:
    * UTF-8
 * Naming:
    * Packages/modules/functions/methods/variables -- lowercase with underscores (e.g. ``can_get_xmp``).
    * Constants -- uppercase with underscores (e.g. ``XMP_NS_AVM`` ).
    * Classes/exceptions -- capitalised words (e.g. ``CrawlerManager``).
 * Imports:
    * Minimise usage of relative imports (may work on development server, but not production server).



Database
--------
* UTF8 encoding
* UTF8 binary collation (otherwise use utf8_english_ci)

Testing
-------

Performance
-----------

HTML
^^^^

Database
^^^^^^^^
* Know what database queries are being executed:
  * How many queries are being executed (any duplication)? 
  * Which indices are being used?
  * Is too much data being retrieved?
* 

Cache
^^^^^
Cache keys



Security
--------
Admin pages over SSL on integration/production servers


HTML
----
Studies have shown that 80% of the end-user response time is spent on the front-end. That means the performance of the website is highly dependent on the HTML/CSS/Javascript. Therefore the following best-practices should be applied (from http://developer.yahoo.com/performance/rules.html):

 * Minimize HTTP Requests
 * Use a Content Delivery Network
 * Add an Expires or a Cache-Control Header
 * Gzip Components
 * Put Scripts at the Bottom
 * Avoid CSS Expressions
 * Make JavaScript and CSS External
 * Reduce DNS Lookups
 * Minify JavaScript and CSS
 * Avoid Redirects
 * Remove Duplicate Scripts
 * Configure ETags
 * Make Ajax Cacheable
 * Flush the Buffer Early
 * Use GET for AJAX Requests
 * Post-load Components
 * Preload Components
 * Reduce the Number of DOM Elements
 * Split Components Across Domains
 * Minimize the Number of iframes
 * No 404s
 * Reduce Cookie Size
 * Use Cookie-free Domains for Components
 * Minimize DOM Access
 * Develop Smart Event Handlers
 * Choose <link> over @import
 * Avoid Filters
 * Optimize Images
 * Optimize CSS Sprites
 * Don't Scale Images in HTML
 * Make favicon.ico Small and Cacheable
 * Keep Components under 25K
 * Pack Components into a Multipart Document

**References:**
 * http://developer.yahoo.com/performance/
