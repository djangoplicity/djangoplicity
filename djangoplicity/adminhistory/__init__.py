# -*- coding: utf-8 -*-
#
# djangoplicity-adminhistory
# Copyright (c) 2007-2011, European Southern Observatory (ESO)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of the European Southern Observatory nor the names
#      of its contributors may be used to endorse or promote products derived
#      from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY ESO ``AS IS'' AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL ESO BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE


"""
Djangoplicity Admin History
===========================
Djangoplicity application that allows super users to browse the history objects that
has been edited via the administration interface.

Install
-------
Add ``djangoplicity.adminhistory` to ``INSTALLED_APPS`` and include the following in your project ``urls.py``::

	urlpatterns += patterns('',
        ( r'^admin/history/', include( 'djangoplicity.adminhistory.urls', namespace="adminhistory_site", app_name="history" ), {} ),
    )

In templates you can link to the view::

    {% url 'adminhistory_site:index' %}


Usage
-----
Go to http://localhost:8000/admin/history/ (or where you decided to install the application). There are now a couple of features:

  * Search will run a free-text search over the username, id, object and action description.
  * Click either the user, action, type or id to filter the objects. Clicking one column after the
    other will filter the already filtered result. Use your browsers back button to go back.
  * Press the edit link to edit the object via the administration interface.
"""
