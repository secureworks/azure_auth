"""
Copyright 2022 Secureworks, Inc.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import json
from django.http import HttpResponse, JsonResponse
from django.template import loader
from azure import settings
from azure.jwt_examples import JWTHandler
from azure.jwt_service_example import JWTServiceExample


def heartbeat(req):
    """Proves that the instances is up for health checkers (NO AZURE)."""
    return JsonResponse({"status": "ok"})


def keep_alive(req):
    """Provide an endpoint where you can renew the access token for the js."""
    return JsonResponse({
        "debug": "Headers updated through this URI only is a good option."
    })


def azure_auth_example(req):
    """Checks out a JWT token in the headers and shows info in the index."""
    template = loader.get_template("azure/index.html")

    # Normally this would come in as "Bearer EncryptedToken"
    token = req.headers.get("Authorization")

    # This is stuff that is often set via an Amazon loadbalancer (AMZN-OIDC-DATA)
    # or in this case set by the resty-openidc docker container in use.
    id_token = req.headers.get("X-HTTP-AUTHORIZATION")
    user = req.headers.get("X-AUTHENTICATED-USER")
    enc_id_token = req.headers.get("X-AMZN-OIDC-DATA")
    if id_token:
        id_token = json.loads(id_token)

    # Showing how to decode an Azure token example using python in case you need
    # to validate something instead of just passing the decrypted user id_token and
    # trusting the service entrypoint to do the work.
    token_decoded, email, error = decode_token_example(enc_id_token)
    user_info = {
        "id_token": id_token,
        "enc_id_token": enc_id_token,
        "username": user,
        "decrypted": token_decoded,
        "OAUTH2_CLIENT_ID": settings.OAUTH2_CLIENT_ID,
        "OAUTH2_TENANT_ID": settings.OAUTH2_TENANT_ID,
        "OAUTH2_AUTHORITY": settings.OAUTH2_AUTHORITY,
        "OAUTH2_JWKS_URI": settings.OAUTH2_JWKS_URI,
        "headers": req.headers,
        "decode_error": error
    }
    return HttpResponse(template.render(user_info, req))


def decode_token_example(token):
    if not token:
        return {"NoToken": "No token found in headers"}, None, None

    # Normally this would be more in the auth middleware but for example:
    return JWTHandler().decode_token(token)


def service_token(req):
    """Show an example of acquiring a service token using the client secret."""
    client = JWTServiceExample()
    client.setup_client()
    access_token = client.connect()
    decoded_token, email, err = JWTHandler().decode_token(access_token)

    return JsonResponse({
        "access_token": access_token,
        "decoded_token": decoded_token,
        "email": email,
        "err": repr(err),
    })
