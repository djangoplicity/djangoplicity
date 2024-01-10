# -*- coding: utf-8 -*-
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from setuptools import setup, find_packages

setup(
    name='djangoplicity',
    version='0.2.0',
    packages=find_packages(include=['djangoplicity', 'djangoplicity.*']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'BeautifulSoup4',
        'django<=3.1',
        'django-ace == 1.0.4',
        'django-mptt == 0.9.1',
        'django-recaptcha == 1.4.0',
        'djangorestframework>=3.14.0,<3.15.0',  # Used for pages, fixed version as 3.6 causes conflict with collectstatic
        'django-signals-ahoy',  # Used by satchmo/models.py
        'django-redis',
        'google-api-python-client>=1.7.4,<=2.92.0',
        'oauth2client',
        'html2text == 3.200.3',
        'htmllaundry == 2.2',
        'lxml == 4.9.3', # Used by htmllaundry
        'icalendar == 3.8',
        'Pillow',
        'pycountry == 1.16',
        'ephem == 3.7.6.0',
        'pysftp',               # Used for contentserver
        'pytest-django',
        'python-dateutil',
        'python-memcached == 1.59',
        'python-xmp-toolkit == 2.0.1',
        'pytz',
        'requests',
        'ndg-httpsclient',  # Extra for requests
        'setuptools',
        'Wand == 0.6.5',
        'piexif',
        'pika == 1.2.1',
        'openpyxl',
        'django-tinymce4-lite == 1.7.2',
        'six == 1.16.0',
        'drf_spectacular>=0.26.2,<0.27.0',
        'django-filter>=21.1,<24.0',
        'python-avm-library @ git+https://github.com/djangoplicity/python-avm-library.git@master#subdirectory=libavm'
    ],
    # metadata for upload to PyPI
    author='European Southern Observatory',
    author_email='information@eso.org',
    description='Djangoplicity',
    license="New BSD License",
    keywords="django djangoplicity",
    url="http://www.djangoplicity.org"
)
