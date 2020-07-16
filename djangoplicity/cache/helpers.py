# -*- coding: utf-8 -*-
#
# djangoplicity-cache
# Copyright (c) 2007-2018, European Southern Observatory (ESO)
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
from __future__ import unicode_literals

from builtins import range
import logging

from django.core.cache import cache


logger = logging.getLogger(__name__)

BASE = 'djp-cache'
MAX_KEYS = 50



def clear_cache(cls):
    '''
    Search for all cache keys for the given class, and clear them
    '''
    key_base = get_cache_key_base(cls)
    if key_base is None:
        logger.error('Could not generate cache key for %s', cls)
        return

    keys = ['{}-{}'.format(key_base, i) for i in range(MAX_KEYS)]

    values = list(cache.get_many(keys).values())
    if values:
        logger.debug('Clearing cache: %s', ', '.join(values))
        cache.delete_many(values)

    cache.delete_many(keys)


def get_cache(key, default=None):
    key = '{}-{}'.format(BASE, key)

    return cache.get(key, default)


def get_cache_key_base(cls):
    try:
        return '-'.join([BASE, cls._meta.app_label,cls._meta.model_name])
    except AttributeError:
        # The given class doesn't have _meta, we return None and leave it
        # to the caller to handle
        return None


def set_cache(key, value, classes, timeout=86400):
    '''
    Save the key/value to the cache, and record the key for each given
    classes so that it can be cleared when any object from the class is saved
    '''
    key = '{}-{}'.format(BASE, key)

    cache.set(key, value, timeout)
    logger.debug('Setting cache: %s', key)

    for cls in classes:
        set_class_cache(cls, key)


def set_class_cache(cls, value):
    '''
    django.core.cache doesn't provide any atomic way of appending to a list
    so instead we use add() which returns True if the key didn't exist, and
    False otherwise, we keep incrementing the key until we find a free one
    '''
    key_base = get_cache_key_base(cls)
    if key_base is None:
        logger.error('Could not generate cache key for %s (%s)', cls, value)
        return

    i = 0
    while True:
        key = '{}-{}'.format(key_base, i)
        if cache.add(key, value):
            break

        logger.info('Key: %s already taken, incrementing', key)
        i += 1
