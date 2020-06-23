from .settings import *

# ENVIRONMENT CONFIG
SITE_ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')
SHORT_NAME = 'Djangoplicity'
TMP_DIR = os.path.join(BASE_DIR, 'tmp')

# APPLICATION DEFINITION
DJANGO_APPS = [
    # Do not autodiscover admin.py modules in all apps because test_project.admin configures custom Admin Sites itself
    # See: https://docs.djangoproject.com/en/1.10/ref/contrib/admin/#discovery-of-admin-files
    'django.contrib.admin.apps.SimpleAdminConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Manage multiple domains content
    'django.contrib.sites',
    # Redirect URLs
    'django.contrib.redirects',
]

DJANGOPLICITY_APPS = [
    # Djangoplicity is an app package itself containing main templates, statics, etc
    'djangoplicity',
    'djangoplicity.menus',
    'djangoplicity.pages',
    'djangoplicity.metadata',
    'djangoplicity.archives',
    'djangoplicity.releases',
    'djangoplicity.media',
    'djangoplicity.announcements',
    'djangoplicity.reports',
    'djangoplicity.utils',
]

THIRD_PARTY_APPS = [
    # WYSIWYG HTML Editor (Used for example in pages editing)
    'tinymce',
]

INSTALLED_APPS = DJANGO_APPS + DJANGOPLICITY_APPS + THIRD_PARTY_APPS

# SITES
SITE_ID=1

if USE_I18N:
    INSTALLED_APPS += [
        'djangoplicity.translation',
    ]

    MIDDLEWARE += [
        # Sets local for request based on URL prefix.
        'djangoplicity.translation.middleware.LocaleMiddleware',  # Request/Response
    ]


# MEDIA
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = "/media/"


# JAVASCRIPT CUSTOM CONFIG
JQUERY_JS = "jquery/jquery-1.11.1.min.js"
JQUERY_UI_JS = "jquery-ui-1.12.1/jquery-ui.min.js"
JQUERY_UI_CSS = "jquery-ui-1.12.1/jquery-ui.min.css"
DJANGOPLICITY_ADMIN_CSS = "djangoplicity/css/admin.css"
DJANGOPLICITY_ADMIN_JS = "djangoplicity/js/admin.js"
SUBJECT_CATEGORY_CSS = "djangoplicity/css/widgets.css"


############
# REPORTS  #
############
REPORTS_DEFAULT_FORMATTER = 'html'
REPORT_REGISTER_FORMATTERS = True


USE_TZ = False

LANGUAGES = [
    ('en', 'English'),
    ('es', 'Spanish'),
]

# ARCHIVES
ARCHIVE_IMPORT_ROOT = os.path.join(BASE_DIR, 'import')
ARCHIVE_ROOT = 'archives/'
IMAGES_ARCHIVE_ROOT = 'archives/images/'
VIDEOS_ARCHIVE_ROOT = 'archives/videos/'
RELEASE_ARCHIVE_ROOT = 'archives/releases/'
ARCHIVE_AUTO_RESOURCE_DELETION = False

ARCHIVES = (
    ('djangoplicity.media.models.Image', 'djangoplicity.media.options.ImageOptions'),
    ('djangoplicity.media.models.Video', 'djangoplicity.media.options.VideoOptions'),
    ('djangoplicity.media.models.VideoSubtitle', 'djangoplicity.media.options.VideoSubtitleOptions'),
    ('djangoplicity.media.models.ImageComparison', 'djangoplicity.media.options.ImageComparisonOptions'),
)

# Allows templates coverage
TEMPLATES[0]['OPTIONS']['debug'] = True

# CELERY
CELERY_IMPORTS = [
    "djangoplicity.archives.contrib.security.tasks",
    "djangoplicity.celery.tasks",
]
# Task result backend
CELERY_RESULT_BACKEND = "amqp"
CELERY_BROKER_URL = 'amqp://guest:guest@broker:5672/'
# Avoid infinite wait times and retries
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'max_retries': 3,
    'interval_start': 0,
    'interval_step': 0.2,
    'interval_max': 0.2,
}
# AMQP backend settings - Required for flower to work as intended
CELERY_RESULT_SERIALIZER = "json"
CELERY_RESULT_EXPIRES = 3600
# File to save revoked tasks across workers restart
CELERY_WORKER_STATE_DB = os.path.join(TMP_DIR, 'celery_states')
CELERY_BEAT_SCHEDULE_FILENAME = os.path.join(TMP_DIR, 'celerybeat_schedule')
