#!/usr/bin/env sh
# Copyright 2022 Secureworks, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
set -eu

echo "From .env Entrypoint: $SERVER_NAME and $INTERNAL_SERVER_NAME"
envsubst '${SERVER_NAME} ${INTERNAL_SERVER_NAME}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

echo "From .env Azure using Client: $OAUTH2_CLIENT_ID for Tenant: $OAUTH2_TENANT_ID and Authority: $AUTH_DNS"
envsubst '${OAUTH2_CLIENT_ID} ${OAUTH2_CLIENT_SECRET} ${AUTH_DNS} ${OAUTH2_TENANT_ID}' < /usr/local/openresty/nginx/conf/azure_sso.template.lua > /usr/local/openresty/nginx/conf/azure_sso.lua

# We could also do all the SSL SERVER_NAME information here but seems excessive.
exec "$@"
