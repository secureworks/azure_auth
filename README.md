# azure_auth

An example of how to build out Azure SSO authentication and the Javascript renewal of credentials for long lived pages / apps.  This should work in Chrome, Firefox, Edge, Brave and Safari but there is currently no Microsoft support for Opera.

Future Improvements in the lua code:
* Ensure the access_token checks id_token.exp, iss, etc
* Restrict the access_token update to only in keep_alive

## Web / Azure Keepalive frontend
There are two docker containers one respresents a webserver that is around to show how to proxy the connection from auth, display login information, AND show the keep alive method using MSAL.js.
This service is meant to be the "internal" facing service that the Auth piece will proxy connections
into.

* It does not require JWT tokens but will show you what the Azure proxy is sending along.
* There is also python code to demonstrate how to deal with a Microsoft Azure token or request one as a service.
* The webserver runs on http://localhost:8000 and has one endpoint that is open access called /heartbeat
which is the kind of thing you need in order to work with a load balancer (aws).

## Azure Authentication using OpenResty lua-resty-openidc and lua-resty-jwt

The Auth container will simply demonstrate how to use Azure login information through an openresty / nginx container.  There are a few important pieces in this config that will hopefully save others time!

* The auth service runs on https://SERVER_NAME:8005 (or change the docker compose).  It will build out a self signed cert using the .env SERVER_NAME variable. 
* No Azure works immediately out of the box you must create an application and create a client secret :(
* If you don't set header max lengths correctly the massive Azure cookie can crash out nginx.
* There is NO built in openidc token refresh using the MSAL.js methods, so it has an option for an Authorization with an AccessToken that is being hacked in the Web javascript.


## Getting started


The first thing to do is ensure you have access to https://portal.azure.com or at least a set of Microsoft
specific UUID's and the client secret for your App registration.  These items will need to be added to the .env
file that is present in the top level of the app (same dir as the docker-compose.yml).

The main pieces you need are TENANT_ID (your org), CLIENT_ID (your app) and the CLIENT_SECRET that proves
your application is actually "the app".  Add these elements into the .env file and configure your SERVER_NAME
environment variable to be what your Azure settings allow in the authentication section.  The OAUTH2_CLIENT_OID
is required only for the service account validation is found describing the very top level Enterprise Application
and is not in the place you would expect in Azure.

ie in the Web Redirect URIs (port required if not on 443):
https://SERVER_NAME:PORT/auth/web/sso

Then under the Single Page Application section you should enable either a keep_alive url or just the root 
of the webserver being fronted by Azure.  This lets us hack in some MSAL.js token keep alive magic:
https://SERVER_NAME:PORT/

Logout is handled by adding an entry in the portal like:
https://SERVER_NAME:PORT/auth/web/sso/logout

```
  # After setting variables in the sample.env and renaming to .env
  docker compose build; docker compose up
```

## Test and Deploy

Use the built-in continuous integration in GitLab or just show it building the docker containers.

**

## Visuals

Add an example of what the UI looks like when it is actually doing JS calls.

## Installation

Copy sample.env to .env and make the required changes.

Once you have entered some of the required Azure configuration into .env just run Make or run docker-compose build.  For local development you will need your SERVER_NAME to actually resolve locally so the easiest thing to do is to edit /etc/hosts and just add a new line "127.0.0.1 SERVER_NAME".

TODO: ADD THE MAKEFILE

## Usage

    $docker-compose up -d
    Then hit either https://SERVER_NAME:PORT for Azure or http://SERVER_NAME:8000 (for debugging/sanity).

## Support

Submit an issue or a pull request.

## Roadmap
If you have ideas for releases in the future, it is a good idea to list them in the README.

## Contributing
Contributions appreciated, pull requests would just go through a review to see if things are working.

## Authors and acknowledgment
Justin Carlson, Brad Crittenden, Robin Koumis (use external facing info?) 

## License
Apache 2.0

## Project status
Example code probably updated once in a while as Azure breaks random things or Browsers decide that popups should also not be allowed to do auth.

Does not work in Opera.
