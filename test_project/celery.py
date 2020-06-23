from __future__ import absolute_import
import sys
import os
from django.conf import settings
from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_project.dp_settings")
app = Celery('test_project')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# A strange bug with Celery makes the first few tasks fail if CONN_MAX_AGE
# is set:
# OperationalError: could not receive data from server: Bad file descriptor
# As a workaround we disable the settings if running in celery
if 'celery' in sys.argv[0]:
   print 'Djangoplicity: Disabling CONN_MAX_AGE'
   settings.DATABASES['default']['CONN_MAX_AGE'] = 0


@app.task(bind=True)
def debug_task(self):
    print 'Request: {0!r}'.format(self.request)
