FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=scheduler_project.settings_prod

# Create and set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        netcat-traditional \
        build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy project files
COPY . .

# Create directories for static files and media
RUN mkdir -p /app/staticfiles /app/media /app/logs

# Create the log file and set proper permissions
RUN touch /app/logs/scheduler.log

# Add startup script (while still root)
COPY ./docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Create a non-root user and switch to it
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
RUN chmod -R 755 /app/logs
USER appuser

# Expose port (Heroku will set the PORT env variable)
EXPOSE $PORT

# Run the application
ENTRYPOINT ["/app/docker-entrypoint.sh"]
