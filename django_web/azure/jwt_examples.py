"""Copyright 2022 Secureworks, Inc.

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


"""These examples show how to use python to validate an encrypted JWT token.

Most likely a service should just trust the auth passthrough to get you a decrypted
id_token and use the roles / issuer from that.  But if you need to also validate this
kind of thing here this can maybe save you some time.
"""
import json
import jwt
import requests
import logging
import base64
from django.conf import settings

# You can grab the jwt token headers and then check the user + roles interactions.
from django.contrib.auth.middleware import RemoteUserMiddleware

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger(__name__)


class JWTHandler(RemoteUserMiddleware):
    """Example of decoding the jwt, it could be used to integrate django auth."""

    def __init__(self):
        """Azure requires a whole lot of config to decode a token."""

        # These keys should get a LONG TERM cache vs just the request.
        self.loaded_keys = None

        self.tenant_id = settings.OAUTH2_TENANT_ID
        self.audience = settings.OAUTH2_CLIENT_ID
        self.jwks_uri = settings.OAUTH2_JWKS_URI
        self.server = settings.OAUTH2_AUTHORITY
        self.issuer = settings.OAUTH2_ISSUER
        self.jwt_algorithms = ["RS256"]

    def load_keys(self):
        """We should be getting the key from Microsofts keys api."""
        response = requests.get(self.jwks_uri, timeout=20)
        response.raise_for_status()
        keys = response.json().get("keys")

        def ensure_bytes(key):
            if isinstance(key, str):
                key = key.encode("utf-8")
            return key

        def decode_value(val):
            decoded = base64.urlsafe_b64decode(ensure_bytes(val) + b"==")
            return int.from_bytes(decoded, "big")

        # It would be nice to just create a string but that doesn't work correctly
        # Or there is some encoding in the json that jacks it up.
        loaded_keys = {}
        for key in keys:
            pem_key = (
                RSAPublicNumbers(n=decode_value(key["n"]), e=decode_value(key["e"]))
                .public_key(default_backend())
                .public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
            )
            loaded_keys[key.get("kid")] = pem_key
        return loaded_keys

    def get_jwt_key_by_kid(self, kid):
        """Lookup a jwt key used by the service for our decoding process."""
        logger.debug(f"Finding Azure key with {kid}")
        if not self.loaded_keys:
            self.loaded_keys = self.load_keys()

        if kid not in self.loaded_keys:
            logger.warn(f"{kid} was not found using {self.jwks_uri}")
        return self.loaded_keys.get(kid)

    def decode_token(self, encoded_token):
        """Attempt to decode the full decoding token."""
        header = self.decode_header(encoded_token)
        jwt_key = self.get_jwt_key_by_kid(header.get("kid"))
        if not jwt_key:
            logger.error(f"Failed to find key from header: {header}")
        return self.decode_jwt(encoded_token, jwt_key)

    def decode_header(self, token):
        """Decode the token header to get the kid for decryption."""
        jwt_headers = token.split(".")[0]
        decoded_jwt_headers = base64.b64decode(jwt_headers)
        decoded_json = json.loads(decoded_jwt_headers)
        return decoded_json

    def decode_jwt(self, encoded_token, secret_or_key):
        """Azure Perform the decoding of the JWT token.

        Return the decoded token and the email associated with the token
        """
        header = None
        token = None
        email = None
        try:
            # Attempt to decode normal user, validating issuer at the same time
            header = self.decode_header(encoded_token)
            logger.debug(f"Azure _decode_jwt {encoded_token} {secret_or_key} {header}")
            token = jwt.decode(
                encoded_token,
                secret_or_key,
                issuer=self.issuer,
                audience=self.audience,
                verify=True,
                algorithms=self.jwt_algorithms,
                leeway=(60 * 10),
            )

            # It would be better if we could figure out how to get the MS Application
            # Token to include role. However I have had NO luck and spent a lot of time.
            email = token.get("preferred_username")
            if not email:
                # We CAN verify the oid is the application env oid ie:
                # token.get("oid") == "Application OID" (pilot|dev)
                # This Object ID can be found be searching the TOP level of Azure and is
                # Normally oid is set to your user name but service access_tokens use
                # the OID of the app whose secret you are using.
                if token.get("oid") == settings.OAUTH2_APP_OID:
                    email = "service_token@yourorg.com"
                    token["preferred_username"] = email
                    token["roles"] = "Set some Application Roles"
                else:
                    raise ValueError(f"Bad JWT token or no username {token}")
        except jwt.exceptions.InvalidIssuerError as jwt_err:
            """Issuer Error."""
            logger.exception(f"Issuer in the token didn't match {self.issuer}")
            return None, None, jwt_err
        except Exception as err:
            logger.exception(f"Invalid JWT {encoded_token} {token} {err}")
            return None, None, err
        logger.debug(
            "User email: %s, decoded_header: %s, decoded token: %s",
            email,
            json.dumps(header),
            json.dumps(token),
        )
        return token, email, None
