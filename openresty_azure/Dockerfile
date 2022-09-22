# Copyright 2022 Secureworks, Inc.
# 
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
# 
#       http://www.apache.org/licenses/LICENSE-2.0
# 
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

FROM openresty/openresty:bullseye-fat

ENV REQUESTS_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

RUN apt update \
    && apt install -y openssl vim wget openresty-opm \
    && rm -rf /var/lib/apt/lists/*
RUN /usr/bin/opm install zmartzone/lua-resty-openidc cdbattags/lua-resty-jwt

# You should probably get a valid cert and use ansible or some DevOps tech to get it either
# on a load balancer, or checked into a code with something like ansible-vault.
ARG SERVER_NAME="SERVER_NAME_FROM.env"
ARG INTERNAL_SERVER_NAME="INTERNAL_SERVER_NAME_FROM.env"

COPY openssl.cnf /tmp/openssl.cnf
RUN echo "$SERVER_NAME with SAN $INTERNAL_SERVER_NAME"
RUN sed -i "s/SERVER_NAME/$SERVER_NAME/" /tmp/openssl.cnf
RUN sed -i "s/INTERNAL_SERVER_NAME/$INTERNAL_SERVER_NAME/" /tmp/openssl.cnf
RUN openssl req -x509 -batch -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/server.key \
    -out /etc/ssl/server.crt \
    -config /tmp/openssl.cnf

# This is mostly all configured and hosted in /usr/local/openresty but the config that defines
# the server is all from /etc/nginx/conf.d 
COPY default.conf.template /etc/nginx/conf.d/
COPY azure_sso.template.lua /usr/local/openresty/nginx/conf/

# In the case of something like an ansible setup for your actual hosts, you can do the
# ansible install for the docker container. If you want to manage certs and secrets 
# with ansible this kind of thing will work if you give the docker --build-arg VAULT_PW=XYZ
# The main bonus is your ansible can also be somewhat tested by dev environments.

# ENV ANSIBLE_VAULT_PASSWORD_FILE=/tmp/.vault_pass
# ARG VAULT_PW="DevCannotBeEmptyOrVaultExplodes"
# ARG PROVISION_TYPE="dev"   # In the case you want to switch ansible files etc.
#COPY ansible ansible/
#WORKDIR "ansible"
#RUN apt install -y python3-pip
#RUN /usr/bin/pip3 install ansible
#RUN echo ${VAULT_PW} > ${ANSIBLE_VAULT_PASSWORD_FILE} && chmod 600 ${ANSIBLE_VAULT_PASSWORD_FILE}
#RUN ANSIBLE_FORCE_COLOR=1 ansible-playbook -e provision_type=$PROVISION_TYPE -i localhost.yml site.yml
#RUN rm ${ANSIBLE_VAULT_PASSWORD_FILE}

COPY docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["/usr/bin/openresty", "-g", "daemon off;"]
STOPSIGNAL SIGQUIT
