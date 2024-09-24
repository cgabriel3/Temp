FROM python:3.9.6-slim-buster

# Set the working directory to /app
WORKDIR /app

COPY . /app

# Install cron command for docker container
RUN apt-get update && apt-get install -y cron

# Install python script dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a cron job to run the python script (run on Friday at 06:00 UTC or 13:00 GMT+7)
# Docker container default timezone is UTC
RUN echo "0 6 * * 5 /usr/local/bin/python /app/activity_report.py >> /var/log/cron.log 2>&1" > /etc/cron.d/activity_report_cronjob
RUN chmod 0644 /etc/cron.d/activity_report_cronjob
RUN crontab /etc/cron.d/activity_report_cronjob

RUN mkdir /script_logs

# Run the command on container startup
CMD ["cron", "-f"]