#!/bin/bash

set -a
# Load environment variables
source .env.config

SUPERSET_USER_IN_DRUID=$1
SUPERSET_PASSWORD_IN_DRUID=$2
# Create superset_user:
curl -u $DRUID_USER:$DRUID_PASSWORD -XPOST http://localhost:8081/druid-ext/basic-security/authentication/db/MyBasicMetadataAuthenticator/users/$SUPERSET_USER_IN_DRUID

# Set password:
data=$(
    jq  --null-input \
        --compact-output \
        --arg password  "$SUPERSET_PASSWORD_IN_DRUID" \
        '{"password": $password}'
)
curl -u $DRUID_USER:$DRUID_PASSWORD -H'Content-Type: application/json' -XPOST -d "$data" http://localhost:8081/druid-ext/basic-security/authentication/db/MyBasicMetadataAuthenticator/users/$SUPERSET_USER_IN_DRUID/credentials

# Create superset role:
curl -u $DRUID_USER:$DRUID_PASSWORD -XPOST http://localhost:8081/druid-ext/basic-security/authorization/db/MyBasicMetadataAuthorizer/roles/superset_role

# Set role permissions
curl -u $DRUID_USER:$DRUID_PASSWORD -H'Content-Type: application/json' -XPOST -d '[{"resource": {"name": ".*","type": "DATASOURCE"},"action": "READ"},{"resource": {"name": ".*","type": "STATE"},"action": "READ"}]' http://localhost:8081/druid-ext/basic-security/authorization/db/MyBasicMetadataAuthorizer/roles/superset_role/permissions

# Create user in authorizer:
curl -u $DRUID_USER:$DRUID_PASSWORD -XPOST http://localhost:8081/druid-ext/basic-security/authorization/db/MyBasicMetadataAuthorizer/users/$SUPERSET_USER_IN_DRUID

# Assign role to user:
curl -u $DRUID_USER:$DRUID_PASSWORD -XPOST http://localhost:8081/druid-ext/basic-security/authorization/db/MyBasicMetadataAuthorizer/users/$SUPERSET_USER_IN_DRUID/roles/superset_role
