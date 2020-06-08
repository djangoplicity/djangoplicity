FROM python:2.7-slim-buster

# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libxml2-dev \
    libxslt-dev

# Create and user user
RUN useradd --create-home djangoplicityadm
ENV USER_HOME=/home/djangoplicityadm
WORKDIR $USER_HOME
USER djangoplicityadm

# Cache requirements and install them
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# scripts installed by pip can be used
ENV PATH=$USER_HOME/.local/bin:$PATH

# final steps
COPY --chown=djangoplicityadm scripts/ scripts/
COPY --chown=djangoplicityadm manage.py manage.py
COPY --chown=djangoplicityadm djangoplicity/ djangoplicity/
COPY --chown=djangoplicityadm tests/ tests/