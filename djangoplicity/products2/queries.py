# -*- coding: utf-8 -*-
#
# djangoplicity-products
# Copyright (c) 2007-2011, European Southern Observatory (ESO)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#
#   * Neither the name of the European Southern Observatory nor the names
#     of its contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
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
#

"""
Definition of special archive queries for product archives
"""

from datetime import datetime
from djangoplicity.archives.contrib.queries import AllPublicQuery, YearQuery
from django.http import Http404


class MessengerQuery(AllPublicQuery):
    def queryset( self, model, options, request, **kwargs ):
        now = datetime.now()
        ( qs, query_data ) = super( MessengerQuery, self ).queryset( model, options, request, **kwargs )
        qs = qs.filter(type='messenger')
        qs = self._filter_datetime( qs, now, 'release_date', False, True )
        qs = self._filter_datetime( qs, now, 'embargo_date', False, True )
        return ( qs, query_data )


class CAPjournalQuery (AllPublicQuery):
    def queryset( self, model, options, request, **kwargs ):
        now = datetime.now()
        ( qs, query_data ) = super( CAPjournalQuery, self ).queryset( model, options, request, **kwargs )
        qs = qs.filter(type='capjournal')
        qs = self._filter_datetime( qs, now, 'release_date', False, True )
        qs = self._filter_datetime( qs, now, 'embargo_date', False, True )
        return ( qs, query_data )


class STECFNewsletterQuery (AllPublicQuery):
    def queryset( self, model, options, request, **kwargs ):
        now = datetime.now()
        ( qs, query_data ) = super( STECFNewsletterQuery, self ).queryset( model, options, request, **kwargs )
        qs = qs.filter(type='stecfnewsletter')
        qs = self._filter_datetime( qs, now, 'release_date', False, True )
        qs = self._filter_datetime( qs, now, 'embargo_date', False, True )
        return ( qs, query_data )


class ScienceInSchoolQuery (AllPublicQuery):
    def queryset( self, model, options, request, **kwargs ):
        now = datetime.now()
        ( qs, query_data ) = super( ScienceInSchoolQuery, self ).queryset( model, options, request, **kwargs )
        qs = qs.filter(type='scienceinschool')
        qs = self._filter_datetime( qs, now, 'release_date', False, True )
        qs = self._filter_datetime( qs, now, 'embargo_date', False, True )
        return ( qs, query_data )


class BulletinQuery (AllPublicQuery):
    def queryset( self, model, options, request, **kwargs ):
        now = datetime.now()
        ( qs, query_data ) = super( BulletinQuery, self ).queryset( model, options, request, **kwargs )
        qs = qs.filter(type='bulletin')
        qs = self._filter_datetime( qs, now, 'release_date', False, True )
        qs = self._filter_datetime( qs, now, 'embargo_date', False, True )
        return ( qs, query_data )


class ElectronicPosterQuery (AllPublicQuery):
    def queryset( self, model, options, request, **kwargs ):
        now = datetime.now()
        ( qs, query_data ) = super( ElectronicPosterQuery, self ).queryset( model, options, request, **kwargs )
        qs = qs.filter(type='E')
        qs = self._filter_datetime( qs, now, 'release_date', False, True )
        qs = self._filter_datetime( qs, now, 'embargo_date', False, True )
        return ( qs, query_data )


class ConferencePosterQuery (AllPublicQuery):
    def queryset( self, model, options, request, **kwargs ):
        now = datetime.now()
        ( qs, query_data ) = super( ConferencePosterQuery, self ).queryset( model, options, request, **kwargs )
        qs = qs.filter(type='C')
        qs = self._filter_datetime( qs, now, 'release_date', False, True )
        qs = self._filter_datetime( qs, now, 'embargo_date', False, True )
        return ( qs, query_data )


class PrintPosterQuery (AllPublicQuery):
    def queryset( self, model, options, request, **kwargs ):
        now = datetime.now()
        ( qs, query_data ) = super( PrintPosterQuery, self ).queryset( model, options, request, **kwargs )
        qs = qs.filter(type='P')
        qs = self._filter_datetime( qs, now, 'release_date', False, True )
        qs = self._filter_datetime( qs, now, 'embargo_date', False, True )
        return ( qs, query_data )


class CalendarYearQuery( YearQuery ):
    def queryset( self, model, options, request, stringparam=None, **kwargs ):
        if not stringparam:
            raise Http404

        now = datetime.now()

        # Convert to year
        try:
            year = int( stringparam )

            # TOOD: Are these constraints really appropriate?
            if year < 1900 or year > now.year + 1:
                raise Http404
        except TypeError:
            raise Http404
        except ValueError:
            raise Http404

        # We want to override the queryset from YearQuery but still use the one
        # from AllPublicQuery, hense we call super(YearQuery, self) and not
        # super(CalendarYearQuery)
        ( qs, _args ) = super( YearQuery, self ).queryset( model, options, request, **kwargs )
        qs = qs.filter( year=year )
        return ( qs, { 'year': year } )
