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
from urllib.parse import urljoin

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from azure import settings


class JWTServiceExample:
    """ This will create a session connected to Azure that you can then use to make
    service calls to your Azure secured app.
    """

    def __init__(self, client_id=None, client_secret=None):
        # Services typically hit this with microsoft (maybe a cross app is different?)
        self.scope = f"{settings.OAUTH2_CLIENT_ID}/.default"

        # Your App must set "accessTokenAcceptedVersion": 2 in manifest or iss is wrong.
        # https://github.com/AzureAD/microsoft-authentication-library-for-js/issues/560
        self.token_url = urljoin(
            f"https://{settings.ISSUER_DNS}",
            f"{settings.OAUTH2_TENANT_ID}/oauth2/v2.0/token"
        )

    def setup_client(self):
        """Creates the session manager that will connect to Azure."""
        client = BackendApplicationClient(client_id=settings.OAUTH2_CLIENT_ID)
        client.prepare_request_body()
        self.session = OAuth2Session(client=client)

    def connect(self):
        """Once connected you can use session to make requests."""
        token_args = self.get_token_request_args()
        self.session.fetch_token(**token_args)
        return self.session.access_token

    def get_token_request_args(self):
        """Probably not all required, some ignored but works with Azure for now."""
        return dict(
            client_id=settings.OAUTH2_CLIENT_ID,
            audience=settings.OAUTH2_CLIENT_ID,
            client_secret=settings.OAUTH2_CLIENT_SECRET,
            tenant_id=settings.OAUTH2_TENANT_ID,
            include_client_id=True,
            scope=self.scope,
            token_url=self.token_url,
        )
