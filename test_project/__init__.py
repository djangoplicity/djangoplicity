from __future__ import absolute_import

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
# This is also required so that infinite waits does not happen when calling celery tasks
from .celery import app as celery_app
