FROM python:2.7-slim-buster

# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libxml2-dev \
    libxslt-dev

RUN mkdir /app
WORKDIR /app

# Cache requirements and install them
COPY requirements/ requirements/
COPY requirements.txt .
RUN pip install -r requirements.txt

# Final required files
COPY scripts/ scripts/
COPY djangoplicity/ djangoplicity/
COPY test_project/ test_project/
COPY setup.cfg .
COPY .coveragerc .
COPY manage.py .
