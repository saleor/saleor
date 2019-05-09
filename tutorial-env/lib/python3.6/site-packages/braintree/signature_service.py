import urllib
from braintree.util.crypto import Crypto

class SignatureService(object):

    def __init__(self, private_key, hashfunc=Crypto.sha1_hmac_hash):
        self.private_key = private_key
        self.hmac_hash = hashfunc

    def sign(self, data):
        equalities = ['%s=%s' % (str(key), str(data[key])) for key in data]
        data_string = '&'.join(equalities)
        return "%s|%s" % (self.hash(data_string), data_string)

    def hash(self, data):
        return self.hmac_hash(self.private_key, data)
