# Build dockerfile to copy all local files & run cron.sh
FROM python:3.7

# Copy all local files to docker image
COPY . /app

# Set working directory
WORKDIR /app

# Install dependencies
RUN pip install -r requirements.txt

# Allow exec permissions on cron.sh and datasources.sh
RUN chmod +x cron.sh
RUN chmod +x datasources.sh