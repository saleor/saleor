from elasticsearch.serializer import JSONSerializer

from .utils import AttrList

class AttrJSONSerializer(JSONSerializer):
    def default(self, data):
        if isinstance(data, AttrList):
            return data._l_
        if hasattr(data, 'to_dict'):
            return data.to_dict()
        return super(AttrJSONSerializer, self).default(data)

serializer = AttrJSONSerializer()
