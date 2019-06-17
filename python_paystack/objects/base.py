'''
base.py
'''
import json
import jsonpickle
from .errors import InvalidInstance
from ..paystack_config import PaystackConfig

class Base():
    '''
    Abstract Base Class
    '''
    def __init__(self):
        if type(self) is Base:
            raise TypeError("Can not make instance of abstract base class")


    def to_json(self, pickled=False):
        '''
        Method to serialize class instance
        '''
        if pickled:
            return jsonpickle.encode(self)
        else:
            data = json.JSONDecoder().decode(jsonpickle.encode(self))
            data.pop("py/object")
            return json.dumps(data)

    @classmethod
    def from_json(cls, data, pickled=False):
        '''
        Method to return a class instance from given json dict
        '''
        class_name = cls.__name__
        class_object = None
        if pickled:
            class_object = jsonpickle.decode(data)
        else:
            py_object = str(cls).replace('<class ', '')
            py_object = py_object.replace('>', '')
            py_object = py_object.replace("'", "")
            data = json.JSONDecoder().decode(data)
            data['py/object'] = py_object
            data = json.JSONEncoder().encode(data)

            class_object = jsonpickle.decode(data)

        if isinstance(class_object, cls):
            return class_object
        else:
            raise InvalidInstance(class_name)

class Manager(Base):
    '''
    Abstract base class for 'Manager' Classes
    '''

    PAYSTACK_URL = None
    SECRET_KEY = None
    LOCAL_COST = None
    INTL_COST = None
    PASS_ON_TRANSACTION_COST = None

    decoder = json.JSONDecoder()

    def __init__(self):
        super().__init__()
        if type(self) is Manager:
            raise TypeError("Can not make instance of abstract base class")

        if not PaystackConfig.SECRET_KEY or not PaystackConfig.PUBLIC_KEY:
            raise ValueError("No secret key or public key found,"
                             "assign values using PaystackConfig.SECRET_KEY = SECRET_KEY and"
                             "PaystackConfig.PUBLIC_KEY = PUBLIC_KEY")

        self.PAYSTACK_URL = PaystackConfig.PAYSTACK_URL
        self.SECRET_KEY = PaystackConfig.SECRET_KEY


    def get_content_status(self, content):
        '''
        Method to return the status and message from an API response

        Arguments :
        content : Response as a dict
        '''

        if  not isinstance(content, dict):
            raise TypeError("Content argument should be a dict")

        return (content['status'], content['message'])

    def parse_response_content(self, content):
        '''
        Method to convert a response's content in bytes to a string.

        Arguments:
        content : Response in bytes
        '''
        content = bytes.decode(content)
        content = self.decoder.decode(content)
        return content

    def build_request_args(self, data=None):
        '''
        Method for generating required headers.
        Returns a tuple containing the generated headers and the data in json.

        Arguments :
        data(Dict) : An optional data argument which holds the body of the request.
        '''
        headers = {'Authorization' : 'Bearer %s' % self.SECRET_KEY,
                   'Content-Type' : 'application/json',
                   'cache-control' : 'no-cache'
                  }

        data = json.dumps(data)

        return (headers, data)
