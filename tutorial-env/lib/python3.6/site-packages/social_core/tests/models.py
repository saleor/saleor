import base64

from ..storage import UserMixin, NonceMixin, AssociationMixin, \
                      CodeMixin, PartialMixin, BaseStorage


class BaseModel(object):
    @classmethod
    def next_id(cls):
        cls.NEXT_ID += 1
        return cls.NEXT_ID - 1

    @classmethod
    def get(cls, key):
        return cls.cache.get(key)

    @classmethod
    def reset_cache(cls):
        cls.cache = {}


class User(BaseModel):
    NEXT_ID = 1
    cache = {}
    _is_active = True

    def __init__(self, username, email=None, **extra_user_fields):
        self.id = User.next_id()
        self.username = username
        self.email = email
        self.password = None
        self.slug = None
        self.social = []
        self.extra_data = {}
        self.extra_user_fields = extra_user_fields
        self.save()

    def is_active(self):
        return self._is_active

    @classmethod
    def set_active(cls, is_active=True):
        cls._is_active = is_active

    def set_password(self, password):
        self.password = password

    def save(self):
        User.cache[self.username] = self


class TestUserSocialAuth(UserMixin, BaseModel):
    NEXT_ID = 1
    cache = {}
    cache_by_uid = {}

    def __init__(self, user, provider, uid, extra_data=None):
        self.id = TestUserSocialAuth.next_id()
        self.user = user
        self.provider = provider
        self.uid = uid
        self.extra_data = extra_data or {}
        self.user.social.append(self)
        TestUserSocialAuth.cache_by_uid[uid] = self

    def save(self):
        pass

    @classmethod
    def reset_cache(cls):
        cls.cache = {}
        cls.cache_by_uid = {}

    @classmethod
    def changed(cls, user):
        pass

    @classmethod
    def get_username(cls, user):
        return user.username

    @classmethod
    def user_model(cls):
        return User

    @classmethod
    def username_max_length(cls):
        return 1024

    @classmethod
    def allowed_to_disconnect(cls, user, backend_name, association_id=None):
        return user.password or len(user.social) > 1

    @classmethod
    def disconnect(cls, entry):
        cls.cache.pop(entry.id, None)
        entry.user.social = [s for s in entry.user.social if entry != s]

    @classmethod
    def user_exists(cls, username):
        return User.cache.get(username) is not None

    @classmethod
    def create_user(cls, username, email=None, **extra_user_fields):
        return User(username=username, email=email, **extra_user_fields)

    @classmethod
    def get_user(cls, pk):
        for username, user in User.cache.items():
            if user.id == pk:
                return user

    @classmethod
    def get_social_auth(cls, provider, uid):
        social_user = cls.cache_by_uid.get(uid)
        if social_user and social_user.provider == provider:
            return social_user

    @classmethod
    def get_social_auth_for_user(cls, user, provider=None, id=None):
        return [usa for usa in user.social
                if provider in (None, usa.provider) and
                id in (None, usa.id)]

    @classmethod
    def create_social_auth(cls, user, uid, provider):
        return cls(user=user, provider=provider, uid=uid)

    @classmethod
    def get_users_by_email(cls, email):
        return [user for user in User.cache.values() if user.email == email]


class TestNonce(NonceMixin, BaseModel):
    NEXT_ID = 1
    cache = {}

    def __init__(self, server_url, timestamp, salt):
        self.id = TestNonce.next_id()
        self.server_url = server_url
        self.timestamp = timestamp
        self.salt = salt

    @classmethod
    def use(cls, server_url, timestamp, salt):
        nonce = TestNonce(server_url, timestamp, salt)
        TestNonce.cache[server_url] = nonce
        return nonce


class TestAssociation(AssociationMixin, BaseModel):
    NEXT_ID = 1
    cache = {}

    def __init__(self, server_url, handle):
        self.id = TestAssociation.next_id()
        self.server_url = server_url
        self.handle = handle

    def save(self):
        TestAssociation.cache[(self.server_url, self.handle)] = self

    @classmethod
    def store(cls, server_url, association):
        assoc = TestAssociation.cache.get((server_url, association.handle))
        if assoc is None:
            assoc = TestAssociation(server_url=server_url,
                                    handle=association.handle)
        assoc.secret = base64.encodestring(association.secret)
        assoc.issued = association.issued
        assoc.lifetime = association.lifetime
        assoc.assoc_type = association.assoc_type
        assoc.save()

    @classmethod
    def get(cls, server_url=None, handle=None):
        result = []
        for assoc in TestAssociation.cache.values():
            if server_url and assoc.server_url != server_url:
                continue
            if handle and assoc.handle != handle:
                continue
            result.append(assoc)
        return result

    @classmethod
    def remove(cls, ids_to_delete):
        assoc = filter(lambda a: a.id in ids_to_delete,
                       TestAssociation.cache.values())
        for a in list(assoc):
            TestAssociation.cache.pop((a.server_url, a.handle), None)


class TestCode(CodeMixin, BaseModel):
    NEXT_ID = 1
    cache = {}

    @classmethod
    def get_code(cls, code):
        for c in cls.cache.values():
            if c.code == code:
                return c


class TestPartial(PartialMixin, BaseModel):
    NEXT_ID = 1
    cache = {}

    def save(self):
        TestPartial.cache[self.token] = self

    @classmethod
    def load(cls, token):
        return cls.cache.get(token)

    @classmethod
    def destroy(cls, token):
        cls.cache.pop(token)


class TestStorage(BaseStorage):
    user = TestUserSocialAuth
    nonce = TestNonce
    association = TestAssociation
    code = TestCode
    partial = TestPartial

    @classmethod
    def is_integrity_error(cls, exception):
        pass
