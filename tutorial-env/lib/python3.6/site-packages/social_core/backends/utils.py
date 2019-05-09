from collections import OrderedDict

from .base import BaseAuth
from ..exceptions import MissingBackend
from ..utils import module_member, user_is_authenticated


# Cache for discovered backends.
BACKENDSCACHE = OrderedDict()


def load_backends(backends, force_load=False):
    """
    Load backends defined on SOCIAL_AUTH_AUTHENTICATION_BACKENDS, backends will
    be imported and cached on BACKENDSCACHE. The key in that dict will be the
    backend name, and the value is the backend class.

    Only subclasses of BaseAuth (and sub-classes) are considered backends.

    Previously there was a BACKENDS attribute expected on backends modules,
    this is not needed anymore since it's enough with the
    AUTHENTICATION_BACKENDS setting. BACKENDS was used because backends used to
    be split on two classes the authentication backend and another class that
    dealt with the auth mechanism with the provider, those classes are joined
    now.

    A force_load boolean argument is also provided so that get_backend
    below can retry a requested backend that may not yet be discovered.
    """
    global BACKENDSCACHE
    if force_load:
        BACKENDSCACHE = OrderedDict()
    if not BACKENDSCACHE:
        for auth_backend in backends:
            backend = module_member(auth_backend)
            if issubclass(backend, BaseAuth):
                BACKENDSCACHE[backend.name] = backend
    return BACKENDSCACHE


def get_backend(backends, name):
    """Returns a backend by name. Backends are stored in the BACKENDSCACHE
    cache dict. If not found, each of the modules referenced in
    AUTHENTICATION_BACKENDS is imported and checked for a BACKENDS
    definition. If the named backend is found in the module's BACKENDS
    definition, it's then stored in the cache for future access.
    """
    try:
        # Cached backend which has previously been discovered
        return BACKENDSCACHE[name]
    except KeyError:
        # Reload BACKENDS to ensure a missing backend hasn't been missed
        load_backends(backends, force_load=True)
        try:
            return BACKENDSCACHE[name]
        except KeyError:
            raise MissingBackend(name)


def user_backends_data(user, backends, storage):
    """
    Will return backends data for given user, the return value will have the
    following keys:
        associated: UserSocialAuth model instances for currently associated
                    accounts
        not_associated: Not associated (yet) backend names
        backends: All backend names.

    If user is not authenticated, then 'associated' list is empty, and there's
    no difference between 'not_associated' and 'backends'.
    """
    available = list(load_backends(backends).keys())
    values = {'associated': [],
              'not_associated': available,
              'backends': available}
    if user_is_authenticated(user):
        associated = storage.user.get_social_auth_for_user(user)
        not_associated = list(set(available) -
                              set(assoc.provider for assoc in associated))
        values['associated'] = associated
        values['not_associated'] = not_associated
    return values
