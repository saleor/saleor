import six


SERIALIZABLE_TYPES = (dict, list, tuple, set, bool, type(None)) + \
                     six.integer_types + six.string_types + \
                     (six.text_type, six.binary_type,)


def is_dict_type(value):
    """Treat any dict, MergeDict, MultiDict instance as dict type"""
    # Check by class name to avoid importing Django MergeDict or
    # Werkzeug MultiDict
    return isinstance(value, dict) or \
        value.__class__.__name__ in ('MergeDict', 'MultiDict')


def partial_prepare(strategy, backend, next_step, user=None, social=None,
                    *args, **kwargs):
    kwargs.update({
        'response': kwargs.get('response') or {},
        'details': kwargs.get('details') or {},
        'username': kwargs.get('username'),
        'uid': kwargs.get('uid'),
        'is_new': kwargs.get('is_new') or False,
        'new_association': kwargs.get('new_association') or False,
        'user': user and user.id or None,
        'social': social and {
            'provider': social.provider,
            'uid': social.uid
        } or None
    })

    clean_args = [strategy.to_session_value(val) for val in args]

    # Clean any MergeDict data type from the values
    clean_kwargs = {}
    for name, value in kwargs.items():
        value = dict(value) if is_dict_type(value) else value
        if isinstance(value, SERIALIZABLE_TYPES):
            clean_kwargs[name] = strategy.to_session_value(value)

    return strategy.storage.partial.prepare(backend.name, next_step, {
        'args': clean_args,
        'kwargs': clean_kwargs
    })


def partial_store(strategy, backend, next_step, user=None, social=None,
                  *args, **kwargs):
    partial = partial_prepare(strategy, backend, next_step, user=user,
                              social=social, *args, **kwargs)
    return strategy.storage.partial.store(partial)


def partial_load(strategy, token):
    partial = strategy.storage.partial.load(token)

    if partial:
        args = partial.args
        kwargs = partial.kwargs.copy()
        user = kwargs.get('user')
        social = kwargs.get('social')

        if isinstance(social, dict):
            kwargs['social'] = strategy.storage.user.get_social_auth(**social)

        if user:
            kwargs['user'] = strategy.storage.user.get_user(user)

        partial.args = [strategy.from_session_value(val) for val in args]
        partial.kwargs = dict((key, strategy.from_session_value(val))
                            for key, val in kwargs.items())
    return partial
