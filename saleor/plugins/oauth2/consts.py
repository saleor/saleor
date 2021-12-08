GOOGLE_URI_MAPPING = {
    "auth": "https://accounts.google.com/o/oauth2/v2/auth",
    "token": "https://oauth2.googleapis.com/token",
    "userinfo": "https://www.googleapis.com/oauth2/v2/userinfo",
}

FACEBOOK_URI_MAPPING = {
    "auth": "https://www.facebook.com/v12.0/dialog/oauth",
    "token": "https://graph.facebook.com/v12.0/oauth/access_token",
    "userinfo": "https://graph.facebook.com/me",
}

URI_MAPPING = {
    "google": GOOGLE_URI_MAPPING,
    "facebook": FACEBOOK_URI_MAPPING,
}
