#!/bin/bash

set -a
# Load environment variables
source .env.config

echo "Creating datasources..."
curl -u $DRUID_USER:$DRUID_PASSWORD -X POST -H 'Content-Type: application/json' -d @car_supervisor.json http://$COORDINATOR_URL/druid/indexer/v1/supervisor

while ! curl -u $DRUID_USER:$DRUID_PASSWORD $COORDINATOR_URL/druid/coordinator/v1/datasources | grep -q car;
    do 
        sleep 3;
        echo "Waiting for car datasource to be ready...";
    done
curl -u $DRUID_USER:$DRUID_PASSWORD -X POST -H 'Content-Type: application/json' -d @bike_supervisor.json http://$COORDINATOR_URL/druid/indexer/v1/supervisor

while ! curl -u $DRUID_USER:$DRUID_PASSWORD $COORDINATOR_URL/druid/coordinator/v1/datasources | grep -q bike;
    do 
        sleep 3;
        echo "Waiting for bike datasource to be ready...";
    done
# Create superset user in Druid
SUPERSET_USER_IN_DRUID=superset_user
SUPERSET_PASSWORD_IN_DRUID=$(date +%s | sha256sum | base64 | head -c 32 ; echo)

./set_druid_user_for_superset.sh $SUPERSET_USER_IN_DRUID $SUPERSET_PASSWORD_IN_DRUID
echo "Utilisateur: superset_user \t Password:" $SUPERSET_PASSWORD_IN_DRUID > password_druid.txt

# Create database and datasets on Superset

source env/bin/activate
python3 deploy_superset.py
