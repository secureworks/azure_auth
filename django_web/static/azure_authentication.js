/**
 * Copyright 2022 Secureworks, Inc.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
 */

/** Expects global MSAL.js to have been loaded in the page
 *
 *  This class will attempt to keep a single page app renewing tokens as long
 *  as possible and provide a login popup if things expire on you.
 *
 *  The sketchy bit is that openidc renewals will not work with a long lived
 *  ajax app, so we have to do MS Azure logins and then provide the auth proxy
 *  backend know the new client tokens obtained via popup.
 *
 *  Flow is:
 *  - Check who the user is (email hint required)
 *  - If found then check the current token exp state and if within our renewal window
 *    attempt to login.
 *  - If not found it will open a loginPopup.
 *  - Send the new token information to the resty-openidc side of things and update that session.
 *  - If popups are NOT enabled at least pop up an alert letting the user know (Brave/Chrome don't)
 */
export class AzureAuth {

    // Might just need the email
    constructor(authId, authority, email, debugDom) {
        this.email = email;
        this.authId = authId;
        this.authority = authority;
        this.debugDom = debugDom;

        // How much leeway before we force the token renewal (useful for testing).
        // Normally the token expires in an hour so to rapidly expire it you can set
        // this to something like 59;
        this.RENEW_IF_EXP_WITHIN_MINUTES = 5;

        this.msalConfig = {
            auth: {
                clientId: authId,
                authority: authority,
            },
            cache: {
                storeAuthStateInCookie: true
            }
        };
        this.msalInstance = new msal.PublicClientApplication(this.msalConfig);
    }

    // For debug purposes so you can see what the ajax is doing.
    msgDom(msg, obj, err) {
        // Really just ugly debug / UI demo.  Normally would not do this but DEMO!
        let domMsg = "Unexpected state";
        if (err) {
            console.error(msg, obj, err);
            domMsg = `${msg} ${err}`;
        } else {
            console.log(msg, obj);
            domMsg = msg || "No message provided?";
        }
        if (!this.debugDom || !msg) {
            return;
        }
        this.debugDom.text(domMsg);
    }

    silentRenewal(cb) {
        // I just need this to set the account object.. maybe
        this.msgDom("Attempting silent renewal of the token");

        // This is only called when our session is getting old on the SERVER (probably)
        // so we force it to renew ahead of time to avoid random js CORS redirect errors.
        this.msalInstance.acquireTokenSilent({
            scopes: ["User.Read", "offline_access", "openid", "profile"],
            cliendId: this.authId,
            forceRefresh: true,
            redirectUri: `${window.location.origin}auth/web/sso`
        }).then(res => {
            this.msgDom("Token Renewal Successful!", res);
            setTimeout(() => {
                this.checkAuthState();
            }, 20 * 1000);

            // Attempt to call the keep_alive endpoint with AccessToken hackery to update
            // the openidc session with the popup acquired access / enc_token.
            this.setHeaderAttempt(res);
            if (typeof cb == "function") {
                cb(res);
            }
        }).catch(err => {
            console.error("Failed to handle silent token renewal", err);
            this.attemptLogin();
        });
    }

    // TODO: Make the keep_alive endpoint potentially be the only valid path for this?
    setHeaderAttempt(res) {
      $.ajax("/keep_alive",
        {
          success: res => {
              this.msgDom("Successfully called the keep_alive endpoint with new tokens.");
          },
          headers: {
              Authorization: `Bearer ${res.idToken}`,
              AccessToken: res.accessToken
          }
      });
    }

    // The full login popup seems to mostly work but the silent token seems
    // to get out of sync with the lua session without our keep alive hackery.
    attemptLogin() {
        this.msgDom("Attempting to check the login state");

        this.msalInstance.loginPopup({
            redirectUri: `${window.location.origin}`
        }).then(res => {
            this.msgDom("Success logging in using a popup!");
            this.msalInstance.setActiveAccount(res.account);

            // Note that YOU must keep checking the authentication state not the lib.
            setTimeout(() => {
                this.checkAuthState();
            }, 10 * 1000);
        }).catch(err => {
            this.msgDom("Failed to authenticate or find user", null, err);
            let errMsg = `
                Login state couldn't be checked or the popup failed to open.
                You may need to enable popups or refresh the page.
            `;
            alert(errMsg);
        });
    }

    checkAuthState() {
        try {
            let account = this.msalInstance.getActiveAccount();
            let expires = moment(account.idTokenClaims.exp * 1000);
            let renewIf = expires.clone().subtract(this.RENEW_IF_EXP_WITHIN_MINUTES, "minutes");
            let current = moment();

            this.msgDom(`Azure MSAL Current Time${current}, renew after ${renewIf} after, expires ${expires}`, account);
            if (current > renewIf) {
                this.silentRenewal();
            } else {
                setTimeout(() => {
                    this.checkAuthState();
                }, 60 * 1000);
            }
        } catch (err) {
            console.error("Failed to check auth state", err);
        }
    }

    start() {
        this.msgDom(`Looking up email ${this.email}`);
        let account = this.msalInstance.getAccountByUsername(this.email);
        if (!account) {
            this.attemptLogin();
        } else {
            this.msalInstance.setActiveAccount(account);
            /*
            // This seems like it should work but currently has frame timeout issues?
            this.msalInstance.ssoSilent({
                loginHint: this.email
            }).then(res => {
                console.log("SSO silent worked", res);
            }).catch(err => {
                console.error("failed to silently sso", err);
            });
            */
            this.checkAuthState();
        }
    }
}
