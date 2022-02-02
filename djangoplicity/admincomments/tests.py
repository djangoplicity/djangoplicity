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

from django.urls.base import reverse
from django.contrib import admin

from djangoplicity.admincomments.admin import AdminCommentMixin, AdminCommentInline
from djangoplicity.test.base_tests import BasicTestCase
from djangoplicity.contrib.admin.sites import AdminSite
from djangoplicity.admincomments.models import AdminComment
from django.contrib.contenttypes.models import ContentType
from faker.factory import Factory
from django.contrib.admin.options import ModelAdmin
from django.forms.models import model_to_dict

try:
    from mock import patch, MagicMock
except ImportError:
    from unittest.mock import patch, MagicMock

fake = Factory.create()


class MockRequest:
    def __init__(self):
        pass


class TestImportAdminViews(BasicTestCase):

    def setUp(self):
        super(TestImportAdminViews, self).setUp()
        self.comment = AdminComment.objects.create(
            comment='This is my comment',
            user=self.admin_user,
            content_type=ContentType.objects.get(model='user'),
            object_id=self.admin_user.id,
            content_object=self.admin_user
        )
        self.site = AdminSite()
        self.request = MockRequest

    def test_model_admin(self):
        ma = ModelAdmin(AdminComment, self.site)
        self.assertEqual(str(ma), 'admincomments.ModelAdmin')
        self.assertEqual(list(ma.get_form(self.request).base_fields), ['comment', 'content_type', 'object_id'])
        self.assertEqual(list(ma.get_fields(self.request)), ['comment', 'content_type', 'object_id'])

    def test_default_attributes(self):
        # test admin attributes
        ma = ModelAdmin(AdminComment, self.site)
        self.assertEqual(ma.actions, [])
        self.assertEqual(ma.inlines, [])

    def test_change_comment(self):
        """
        Test comment admin page get and post
        """
        # get admin page
        url = reverse('admin:admincomments_admincomment_change', args=[self.comment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # set a change and send
        self.comment.comment += 'add change'
        data = model_to_dict(self.comment)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

    def test_admin_comment_mixin(self):
        """
        Test Inline admin mixin for integrate the admin comments into for
        your django model.
        """
        formset_mock = MagicMock()
        data = model_to_dict(self.comment)

        class TestAdmin(AdminCommentMixin, admin.ModelAdmin):
            inlines = [AdminCommentInline]

        ma = TestAdmin(AdminComment, self.site)
        ma.save_formset(MagicMock(), self.comment, formset_mock, data)
        formset_mock.save_m2m.assert_called_once_with()
