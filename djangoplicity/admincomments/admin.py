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
#

from django import forms
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.db import models
from djangoplicity.admincomments.models import AdminComment


class AdminCommentInline( GenericTabularInline ):
    """
    Inline admin for integrate the admin comments into for
    your django model.

    Just add ``AdminCommentInline`` to the list of inlines
    for your admin::

        from djangoplicity.admincomments.admin import AdminCommentInline
        class SomeModelAdmin( AdminCommentMixin, ModelAdmin ):
            ...
            inlines = [ AdminCommentInline, ... ]
    """
    model = AdminComment
    extra = 1
    formfield_overrides = {
        models.TextField: { 'widget': forms.Textarea( attrs={'rows': '3', 'cols': '70'} ) }
    }


class AdminCommentMixin( admin.ModelAdmin ):
    inlines = [AdminCommentInline]

    def save_formset( self, request, form, formset, change ):
        """
        Given an inline formset save it to the database.
        """
        objects = formset.save( commit=False )
        for obj in objects:
            obj.user = request.user
            obj.save()
        for obj in formset.deleted_objects:
            obj.delete()
        formset.save_m2m()


class AdminCommentOptions( admin.ModelAdmin ):
    list_display = ( 'timestamp', 'user', 'comment', 'content_type', 'object_id' )
    list_filter = ( 'timestamp', 'content_type' )
    search_fields = ( 'comment', 'object_id' )
    date_hierarchy = 'timestamp'
    fieldsets = (
        ( None, {
            'fields': ( 'timestamp', 'user', 'comment', )
        } ),
        ( 'Related object', {
            'fields': ( 'content_type', 'object_id', 'content_object' )
        } ),
    )
    readonly_fields = ( 'timestamp', 'user', 'comment', 'content_type', 'object_id', 'content_object', )

    def save_model( self, request, obj, form, change ):
        """ Attach the user to then current object being saved """
        obj.user = request.user
        obj.save()


def register_with_admin( admin_site ):
    admin_site.register( AdminComment, AdminCommentOptions )

register_with_admin( admin.site )
