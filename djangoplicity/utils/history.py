# -*- coding: utf-8 -*-
#
# Djangoplicity
# Copyright 2007-2015 ESA/Hubble
#
# Authors:
#   Mathias André <mandre@eso.org>

from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType


def add_admin_history(instance, message, user=None, flag='CHANGE'):
    '''
    Add a change message to the instance admin history
    '''
    if not user:
        user, _created = User.objects.get_or_create(username='djangoplicity')

    if flag == 'ADDITION':
        flag = ADDITION
    elif flag == 'DELETION':
        flag = DELETION
    else:
        flag = CHANGE

    LogEntry.objects.log_action(
        user_id=user.pk,
        content_type_id=ContentType.objects.get_for_model(instance).pk,
        object_id=instance.pk,
        object_repr=unicode(instance),
        action_flag=flag,
        change_message=message
    )
