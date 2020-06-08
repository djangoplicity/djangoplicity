FROM python:2.7-slim-buster

# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libxml2-dev \
    libxslt-dev

RUN mkdir /app
WORKDIR /app

# Cache requirements and install them
COPY requirements.txt .
RUN pip install -r requirements.txt

# final steps
COPY scripts/ scripts/
COPY manage.py manage.py
COPY djangoplicity/ djangoplicity/
COPY tests/ tests/
COPY setup.cfg .