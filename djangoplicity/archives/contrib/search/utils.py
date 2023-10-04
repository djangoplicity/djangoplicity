# -*- coding: utf-8 -*-
#
# djangoplicity-archives
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

from django.core.cache import cache
from django.db.utils import DatabaseError

from djangoplicity.metadata.models import Facility, Instrument, \
    TaxonomyHierarchy, SubjectName, Category

CACHE_TIMEOUT = 300


def _get_facilities():
    key = __name__ + '_get_facilities'
    res = cache.get(key)

    if not res:
        try:
            res = [( i.id, i.name ) for i in Facility.objects.filter( published=True ).order_by( 'name' )]
        except DatabaseError:
            res = []

        cache.set(key, res, CACHE_TIMEOUT)

    return res


def _get_instruments():
    key = __name__ + '_get_instruments'
    res = cache.get(key)

    if not res:
        try:
            return [( i.id, i.name ) for i in Instrument.objects.filter( published=True )]
        except DatabaseError:
            return []

        cache.set(key, res, CACHE_TIMEOUT)

    return res


def _get_categories():
    key = __name__ + '_get_categories'
    res = cache.get(key)

    if not res:
        try:
            return [( i.id, i.name ) for i in TaxonomyHierarchy.objects.exclude( level1=101 )]
        except DatabaseError:
            return []

        cache.set(key, res, CACHE_TIMEOUT)

    return res


def _get_web_categories(category_type):
    key = __name__ + '_get_web_categories__' + category_type
    res = cache.get(key)

    if not res:
        try:
            return [( i.id, i.name ) for i in Category.objects.filter(type__name=category_type)]
        except DatabaseError:
            return []

        cache.set(key, res, CACHE_TIMEOUT)

    return res


def _get_snames():
    key = __name__ + '_get_snames'
    res = cache.get(key)

    if not res:
        try:
            return [( i.id, i.name ) for i in SubjectName.objects.all()]
        except DatabaseError:
            return []

        cache.set(key, res, CACHE_TIMEOUT)

    return res
