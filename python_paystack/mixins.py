'''

'''
import json
import requests

from .objects.errors import APIConnectionFailedError

class CreatableMixin(object):
    def create(self, target_object):
        '''

        '''
        url = self.PAYSTACK_URL + self._endpoint

        data = target_object.to_json()        
        headers, _ = self.build_request_args()        
        response = requests.post(url, headers=headers, data=data)
        
        content = response.content
        content = self.parse_response_content(content)        
        status, message = self.get_content_status(content)

        if status:
            data = json.dumps(content['data'])
            return self._object_class.from_json(data)
        else:
            raise APIConnectionFailedError(message)


class RetrieveableMixin(object):
    '''

    '''
        
    def get_all(self):
        '''

        '''
        headers, _ = self.build_request_args()
        response = requests.get(self.PAYSTACK_URL + self._endpoint, headers=headers)

        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)

        if status:
            data = content['data']
            meta = content['meta']
            objects = []
            for item in data:
                item = json.dumps(item)                
                objects.append(self._object_class.from_json(item))
                return (objects, meta)
        else:
            raise APIConnectionFailedError(message)

        
    def get(self, object_id):
        '''
        Method for getting an object with the specified id
        '''
        headers, _ = self.build_request_args()

        url = "%s%s/%s" % (self.PAYSTACK_URL, self._endpoint, object_id)
        response = requests.get(url, headers=headers)

        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)

        if status:
            data = json.dumps(content['data'])            
            return self._object_class.from_json(data)
        else:
            raise APIConnectionFailedError(message)


class UpdateableMixin(object):
    def update(self, object_id, updated_object):
        '''
        Method for updating existing plan
        '''
        if not isinstance(updated_object, self._object_class):
            raise TypeError

        data = updated_object.to_json()
        headers, _ = self.build_request_args()
        url = "%s%s/%s" % (self.PAYSTACK_URL, self._endpoint, object_id)

        response = requests.put(url, headers=headers, data=data)
        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)
        if status or message:
            return (status, message)
        else:
            raise APIConnectionFailedError(message)