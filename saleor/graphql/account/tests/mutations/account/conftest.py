REQUEST_EMAIL_CHANGE_QUERY = """
mutation requestEmailChange(
    $password: String!, $new_email: String!, $redirect_url: String!, $channel:String
) {
    requestEmailChange(
        password: $password,
        newEmail: $new_email,
        redirectUrl: $redirect_url,
        channel: $channel
    ) {
        user {
            email
        }
        errors {
            code
            message
            field
        }
  }
}
"""

CONFIRM_EMAIL_UPDATE_QUERY = """
mutation emailUpdate($token: String!, $channel: String) {
    confirmEmailChange(token: $token, channel: $channel){
        user {
            email
        }
        errors {
            code
            message
            field
        }
  }
}
"""
