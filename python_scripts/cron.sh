#!/bin/bash

set -a
# Load environment variables
source .env.config

# Compute hash for AKHQ Password
echo $AKHQ_PASSWORD
AKHQ_PASSWORD_HASH=$(echo -n $AKHQ_PASSWORD | sha256sum | sed "s/  -//g")
echo $AKHQ_PASSWORD_HASH

# # Create datasources in Druid
echo $COORDINATOR_URL
echo "Waiting for Druid to be ready... $COORDINATOR_URL"

while ! curl $COORDINATOR_URL/status/health;
    do 
        sleep 3;
        echo "Waiting for Druid to be ready...";
    done

# # Launch the cron
# source env/bin/activate
echo "Running cron"
python3 cron.py 