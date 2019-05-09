import re
import string
import sys
from braintree.attribute_getter import AttributeGetter

text_type = unicode if sys.version_info[0] == 2 else str
raw_type = str if sys.version_info[0] == 2 else bytes

class Resource(AttributeGetter):
    @staticmethod
    def verify_keys(params, signature):
        allowed_keys = Resource.__flattened_signature(signature)
        params_keys = Resource.__flattened_params_keys(params)

        invalid_keys = [key for key in params_keys if key not in allowed_keys]
        invalid_keys = Resource.__remove_wildcard_keys(allowed_keys, invalid_keys)

        if len(invalid_keys) > 0:
            keys_string = ", ".join(invalid_keys)
            raise KeyError("Invalid keys: " + keys_string)

    @staticmethod
    def __flattened_params_keys(params, parent=None):
        if isinstance(params, text_type) or isinstance(params, raw_type):
            return [ "%s[%s]" % (parent, params) ]
        else:
            keys = []
            for key, val in params.items():
                full_key = "%s[%s]" % (parent, key) if parent else key
                if isinstance(val, dict):
                    keys += Resource.__flattened_params_keys(val, full_key)
                elif isinstance(val, list):
                    for item in val:
                        keys += Resource.__flattened_params_keys(item, full_key)
                else:
                    keys.append(full_key)
            return keys

    @staticmethod
    def __flattened_signature(signature, parent=None):
        flat_sig = []
        for item in signature:
            if isinstance(item, dict):
                for key, val in item.items():
                    full_key = '{0}[{1}]'.format(parent, key) if parent else key
                    flat_sig += Resource.__flattened_signature(val, full_key)
            else:
                full_key = '{0}[{1}]'.format(parent, item) if parent else item
                flat_sig.append(full_key)
        return flat_sig

    @staticmethod
    def __remove_wildcard_keys(allowed_keys, invalid_keys):
        wildcard_keys = [re.sub("(?<=[^\\\\])_", "\\_", re.escape(key)).replace("\\[\\_\\_any\\_key\\_\\_\\]", "\\[[\w-]+\\]") for key in allowed_keys if re.search("\\[__any_key__\\]", key)]
        new_keys = []
        for key in invalid_keys:
            if len([match for match in wildcard_keys if re.match("\A" + match + "\Z", key)]) == 0:
                new_keys.append(key)
        return new_keys

    def __init__(self, gateway, attributes):
        AttributeGetter.__init__(self, attributes)
        self.gateway = gateway

