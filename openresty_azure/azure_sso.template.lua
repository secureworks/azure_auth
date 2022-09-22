# Copyright 2022 Secureworks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

access_by_lua_block {
    local req_host = ngx.req.get_headers().host
    -- Remember, each entry in opts must end with a comma, except the last one.
    local opts = {
        -- discovery includes the azure tenant id. do not change
        discovery = "https://${AUTH_DNS}/${OAUTH2_TENANT_ID}/v2.0/.well-known/openid-configuration",

        -- AZURE WILL NOT WORK LOCALLY TILL YOU ENTER THESE
        -- insert your azure app config here the client_id and secret can come from the param store in AWS
        -- This is a new client id / secret I generated, will nuke once it all works.
        client_id = "${OAUTH2_CLIENT_ID}",
        client_secret = "${OAUTH2_CLIENT_SECRET}",

        -- Secret client post will be selected as the default method
        -- token_endpoint_auth_method = "private_key_jwt",
        token_endpoint_auth_method = "client_secret_post",
        redirect_uri = "https://" .. req_host .. "/auth/web/sso",
        logout_path = "/auth/web/sso/logout",

        -- User.Read is default azure, openid is needed for RS256 id_tokens, otherwise alg will be None
        scope = "User.Read offline_access openid profile",

        -- Azure session seems to set a valid token for about 1hr
        -- https://github.com/zmartzone/lua-resty-openidc/issues/66
        try_to_renew = true,
        renew_access_token_on_expiry = true,
        access_token_expires_leeway = 120,

        -- Do not refresh the session in this way or it can randomly fail your ajax
        -- calls if the front end is handling the refresh of the tokens.
        -- refresh_session_interval = 3600,

        --must have lua_ssl_trusted_certificate set correctly
        ssl_verify = "yes",

        -- must set accept_none_alg to true if you do not include the openid scope
        accept_none_alg = false,
        token_signing_alg_values_expected = { "RS256" },

        -- for testing set to true
        force_reauthorize = false,

        -- session_contents can include: id_token, enc_id_token, access_token (includes refresh token)
        session_contents = {access_token=true, id_token=true, enc_id_token=true}

        -- not including both proxy types will cause proxy functionality to fail
        -- proxy_opts = {
        --     http_proxy = "http://gateway.zscalerthree.net:9480",
        --     https_proxy = "http://gateway.zscalerthree.net:9480"
        -- }
    }
    -- imports oidc, cjson
    local oidc = require("resty.openidc")
    local cjson = require "cjson"

    -- Uncomment for debug logging!  As a Demo showing all logging by default :)
    oidc.set_logging(nil, { DEBUG = ngx.STDERR })

    local result, session
    local enc_id_token, id_token, access_token

    local ah = ngx.req.get_headers()
    local auth = ah["Authorization"]
    if auth and string.find(auth, "Bearer ") then
       ngx.log(ngx.DEBUG, "Trying to validate Bearer JWT token")

       id_token, err = oidc.bearer_jwt_verify(opts)
       if err or not id_token then
         ngx.status = 403
         ngx.log(ngx.STDERR, err)
         ngx.exit(ngx.HTTP_FORBIDDEN)
       end
       ngx.log(ngx.DEBUG, "ID Bearer token was valid" .. cjson.encode(id_token))

       -- Getting a bit ugly.  Still kinda shocked there is no split method.
       enc_id_token = string.match(auth, "Bearer (.+)")

       -- We want to get the user session and probably update the tokens
       -- This block could be done only on specific request_uri (ie: keep_alive)
       r_session = require("resty.session")
       session, session_err = r_session.start()
       if session then
           -- ngx.log(ngx.STDERR, cjson.encode(session.data.id_token))
           -- CHECK that the session.data has the same id_token.preferred_username AND that
           -- the iss is the same in the token, this is basically an update via MSAL path. 
           -- Could also check the exp of the new token is larger than the old.
           ngx.log(ngx.DEBUG, "Setting JWT bearer token into session" .. cjson.encode(session.data.id_token))
           -- session.data.state
           session.data.enc_id_token = enc_id_token
           session.data.id_token = id_token

           -- This can be passed in by the javascript so that we can update our session using MSAL
           access_token = ah["AccessToken"]
           if access_token then
              session.data.access_token = access_token
              ngx.log(ngx.DEBUG, "Access token saved to session")
           end
       else
           ngx.log(ngx.ERROR, "Could not start session around bearer token updating.")
       end
       session:save()
       session:close()
    else
        -- authenticate must be called to initiate auth or refresh process
        -- result includes keys ["id_token", "access_token", "enc_id_token"]
        ngx.log(ngx.DEBUG, "Attempting to check authentication state in Azure with authenticate()")
        result, auth_error, target_url, session = oidc.authenticate(opts)
        if auth_error then
            ngx.status = 403
            ngx.say(auth_error)
            ngx.exit(ngx.HTTP_FORBIDDEN)
        end
        ngx.log(ngx.DEBUG, "Full Authenticate used" .. cjson.encode(result))
        enc_id_token = session.data.enc_id_token
        id_token = session.data.id_token
        access_token = session.data.access_token
        session:close()
    end
    ngx.log(ngx.DEBUG, "Successfully passed auth.")

    -- session.data contains values set in the above session_contents option
    -- uncomment to print various fields to nginx error log
    -- id_token is the most useful, it is the decrypted jwt token
    -- ngx.log(ngx.STDERR, cjson.encode(session.data.id_token))
    -- ngx.log(ngx.STDERR, cjson.encode(session.data.refresh_token))
    -- ngx.log(ngx.STDERR, cjson.encode(session.data.access_token))
    -- ngx.log(ngx.STDERR, cjson.encode(session.data.enc_id_token))
    -- ngx.log(ngx.STDERR, cjson.encode(session.data.id_token.preferred_username))

    -- SET REQUEST HEADERS SENT TO DJANGO
    -- ngx.log(ngx.STDERR, "ID Token: " .. cjson.encode(id_token))
    -- ngx.log(ngx.STDERR, "Access Token: " .. cjson.encode(access_token))
    ngx.req.set_header("X-ACCESS-TOKEN", access_token)
    ngx.req.set_header("X-AUTHENTICATED-USER", id_token.preferred_username)
    ngx.req.set_header("X-APPLICATION-ID", id_token.aud)
    ngx.req.set_header("X-AUTH-IP-ADDRESS", id_token.ipaddr)

    -- setting sketchy headers that are a little oddly specific to an AWS LB
    ngx.req.set_header("X-AMZN-OIDC-DATA", enc_id_token)
    ngx.req.set_header("X-HTTP-AUTHORIZATION", cjson.encode(id_token))

    -- All the token information is actually unencrypted by lua but our JWT freaks

    -- SET RESPONSE HEADERS
    --ngx.header["Server"] = "nginx"
}
