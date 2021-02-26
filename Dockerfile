FROM python:2.7-slim-buster

# See: https://docs.python.org/3/using/cmdline.html#cmdoption-u
ENV PYTHONUNBUFFERED=1

# Install dependencies
# - imagemagick is used for process images and generate derivatives
# - libldap-2.4-2 are runtime libraries for the OpenLDAP use by django-auth-ldap
# - cssmin and node-uglify are the processors used by django pipeline
# - ffmpeg and mplayer are required for videos processing
# - procps is just for development to use pkill in the management command: runcelery
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    libxml2-dev \
    libxslt-dev \
    imagemagick-6.q16 \
    libldap-2.4-2 \
    cssmin \
    node-uglify \
    ffmpeg \
    mplayer \
    procps

RUN mkdir /app
WORKDIR /app

# Cache requirements and install them
COPY requirements/ requirements/
COPY requirements.txt .
RUN pip install -r requirements.txt --find-links https://www.djangoplicity.org/repository/packages/

# Create app required directories
RUN mkdir -p tmp

# Final required files
COPY scripts/ scripts/
COPY djangoplicity/ djangoplicity/
COPY test_project/ test_project/
COPY .coveragerc .
COPY manage.py .
