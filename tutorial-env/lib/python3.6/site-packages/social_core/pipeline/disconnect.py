from ..exceptions import NotAllowedToDisconnect


def allowed_to_disconnect(strategy, user, name, user_storage,
                          association_id=None, *args, **kwargs):
    if not user_storage.allowed_to_disconnect(user, name, association_id):
        raise NotAllowedToDisconnect()


def get_entries(strategy, user, name, user_storage, association_id=None,
                *args, **kwargs):
    return {
        'entries': user_storage.get_social_auth_for_user(
            user, name, association_id
        )
    }


def revoke_tokens(strategy, entries, *args, **kwargs):
    revoke_tokens = strategy.setting('REVOKE_TOKENS_ON_DISCONNECT', False)
    if revoke_tokens:
        for entry in entries:
            if 'access_token' in entry.extra_data:
                backend = entry.get_backend(strategy)(strategy)
                backend.revoke_token(entry.extra_data['access_token'],
                                     entry.uid)


def disconnect(strategy, entries, user_storage, *args, **kwargs):
    for entry in entries:
        user_storage.disconnect(entry)
