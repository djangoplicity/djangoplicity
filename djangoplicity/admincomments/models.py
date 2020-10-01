# -*- coding: utf-8 -*-
#
# djangoplicity-admincomments
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

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class AdminComment( models.Model ):
    """
    Generic modelf for storing comments about another object. Most useful as
    a sort of change log for admin interface.
    """

    # Timestamp of comment
    timestamp = models.DateTimeField( auto_now_add=True )

    # Comment
    comment = models.TextField( blank=True )

    # User who created the comment - is set automatically by admin form
    user = models.ForeignKey( User, null=True, blank=True, editable=False )

    # Content type of generic relation - see content types framework
    content_type = models.ForeignKey( ContentType )

    # Object id of generic relation (using slug to allow relations to models with Char PK) - see content types framework
    object_id = models.SlugField()

    # Generic foreign key to object being commented on - see content types framework
    content_object = GenericForeignKey( 'content_type', 'object_id' )

    def __str__(self):
        ctx = { 'timestamp': self.timestamp.isoformat(), 'content_type': self.content_type, 'username': self.user.username if self.user else '' }
        if self.user:
            return u"%(timestamp)s: %(content_type)s comment by %(username)s" % ctx
        else:
            return u"%(timestamp)s: %(content_type)s comment" % ctx

    class Meta:
        ordering = ['-timestamp', 'content_type', 'object_id' ]
