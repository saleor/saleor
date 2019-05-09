from __future__ import absolute_import, division, print_function

from stripe import api_requestor, util
from stripe.six.moves.urllib.parse import quote_plus


def nested_resource_class_methods(resource, path=None, operations=None):
    if path is None:
        path = "%ss" % resource
    if operations is None:
        raise ValueError("operations list required")

    def wrapper(cls):
        def nested_resource_url(cls, id, nested_id=None):
            url = "%s/%s/%s" % (
                cls.class_url(),
                quote_plus(id),
                quote_plus(path),
            )
            if nested_id is not None:
                url += "/%s" % quote_plus(nested_id)
            return url

        resource_url_method = "%ss_url" % resource
        setattr(cls, resource_url_method, classmethod(nested_resource_url))

        def nested_resource_request(
            cls,
            method,
            url,
            api_key=None,
            idempotency_key=None,
            stripe_version=None,
            stripe_account=None,
            **params
        ):
            requestor = api_requestor.APIRequestor(
                api_key, api_version=stripe_version, account=stripe_account
            )
            headers = util.populate_headers(idempotency_key)
            response, api_key = requestor.request(method, url, params, headers)
            return util.convert_to_stripe_object(
                response, api_key, stripe_version, stripe_account
            )

        resource_request_method = "%ss_request" % resource
        setattr(
            cls, resource_request_method, classmethod(nested_resource_request)
        )

        for operation in operations:
            if operation == "create":

                def create_nested_resource(cls, id, **params):
                    url = getattr(cls, resource_url_method)(id)
                    return getattr(cls, resource_request_method)(
                        "post", url, **params
                    )

                create_method = "create_%s" % resource
                setattr(
                    cls, create_method, classmethod(create_nested_resource)
                )

            elif operation == "retrieve":

                def retrieve_nested_resource(cls, id, nested_id, **params):
                    url = getattr(cls, resource_url_method)(id, nested_id)
                    return getattr(cls, resource_request_method)(
                        "get", url, **params
                    )

                retrieve_method = "retrieve_%s" % resource
                setattr(
                    cls, retrieve_method, classmethod(retrieve_nested_resource)
                )

            elif operation == "update":

                def modify_nested_resource(cls, id, nested_id, **params):
                    url = getattr(cls, resource_url_method)(id, nested_id)
                    return getattr(cls, resource_request_method)(
                        "post", url, **params
                    )

                modify_method = "modify_%s" % resource
                setattr(
                    cls, modify_method, classmethod(modify_nested_resource)
                )

            elif operation == "delete":

                def delete_nested_resource(cls, id, nested_id, **params):
                    url = getattr(cls, resource_url_method)(id, nested_id)
                    return getattr(cls, resource_request_method)(
                        "delete", url, **params
                    )

                delete_method = "delete_%s" % resource
                setattr(
                    cls, delete_method, classmethod(delete_nested_resource)
                )

            elif operation == "list":

                def list_nested_resources(cls, id, **params):
                    url = getattr(cls, resource_url_method)(id)
                    return getattr(cls, resource_request_method)(
                        "get", url, **params
                    )

                list_method = "list_%ss" % resource
                setattr(cls, list_method, classmethod(list_nested_resources))

            else:
                raise ValueError("Unknown operation: %s" % operation)

        return cls

    return wrapper
