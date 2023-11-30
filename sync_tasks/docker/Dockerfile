FROM python:3.9.6-slim-buster

# Set the working directory to /app
WORKDIR /app

COPY ../.. /app

# Install cron command for docker container
RUN apt-get update && apt-get install -y cron

# Install python script depedencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a cron job to run the python script (every 03:00 UTC or 10:00 GMT+7)
# Docker container default timezone is UTC
RUN echo "0 3 * * * /usr/local/bin/python /app/sync_tasks.py >> /var/log/cron.log 2>&1" > /etc/cron.d/sync_tasks_cronjob
RUN chmod 0644 /etc/cron.d/sync_tasks_cronjob
RUN crontab /etc/cron.d/sync_tasks_cronjob

RUN mkdir /script_logs

# Run the command on container startup
CMD ["cron", "-f"]