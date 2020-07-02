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
        'django-ace == 1.0.4',
        'django-mptt == 0.9.1',
        'django-recaptcha == 1.4.0',
        'djangorestframework == 3.8.2',  # Used for pages, fixed version as 3.6 causes conflict with collectstatic
        'django-signals-ahoy',  # Used by satchmo/models.py
        'django-redis',
        'google-api-python-client == 1.7.4',
        'oauth2client',
        'html2text == 3.200.3',
        'htmllaundry',
        'ipython == 5.5.0',  # Last version compatible with python 2.7
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
        'Wand == 0.4.4',
        'piexif',
        'pika',
        'openpyxl',
        'django-tinymce4-lite == 1.7.2',
    ],
    dependency_links=[
        'https://github.com/esoobservatory/python-avm-library/tarball/master#egg=python-avm-library-1.0b3',
    ],
    # metadata for upload to PyPI
    author='European Southern Observatory',
    author_email='information@eso.org',
    description='Djangoplicity',
    license="New BSD License",
    keywords="django djangoplicity",
    url="http://www.djangoplicity.org"
)
