FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install gunicorn daphne whitenoise

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migration and start server
CMD python manage.py migrate --noinput && daphne -b 0.0.0.0 -p $PORT chat_project.asgi:application
