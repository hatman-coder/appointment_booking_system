FROM nginx/unit:1.28.0-python3.10

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory early
WORKDIR /code

# Copy and install dependencies
COPY ./requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files after dependencies are installed
COPY . /code

# Create necessary directories (if required)
RUN mkdir -p /srv/www/mas

# Copy static files into the server folder
COPY static /srv/www/mas/

# Apply migrations and collect static files
RUN python manage.py makemigrations && \
    python manage.py migrate && \
    python manage.py collectstatic --no-input

# Use Gunicorn as the application server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]
