from graphql_relay import to_global_id

from ...types import ID, NonNull, ObjectType, String
from ...types.definitions import GrapheneObjectType
from ..node import GlobalID, Node


class CustomNode(Node):
    class Meta:
        name = "Node"


class User(ObjectType):
    class Meta:
        interfaces = [CustomNode]

    name = String()


class Info(object):
    def __init__(self, parent_type):
        self.parent_type = GrapheneObjectType(
            graphene_type=parent_type,
            name=parent_type._meta.name,
            description=parent_type._meta.description,
            fields=None,
            is_type_of=parent_type.is_type_of,
            interfaces=None,
        )


def test_global_id_defaults_to_required_and_node():
    gid = GlobalID()
    assert isinstance(gid.type, NonNull)
    assert gid.type.of_type == ID
    assert gid.node == Node


def test_global_id_allows_overriding_of_node_and_required():
    gid = GlobalID(node=CustomNode, required=False)
    assert gid.type == ID
    assert gid.node == CustomNode


def test_global_id_defaults_to_info_parent_type():
    my_id = "1"
    gid = GlobalID()
    id_resolver = gid.get_resolver(lambda *_: my_id)
    my_global_id = id_resolver(None, Info(User))
    assert my_global_id == to_global_id(User._meta.name, my_id)


def test_global_id_allows_setting_customer_parent_type():
    my_id = "1"
    gid = GlobalID(parent_type=User)
    id_resolver = gid.get_resolver(lambda *_: my_id)
    my_global_id = id_resolver(None, None)
    assert my_global_id == to_global_id(User._meta.name, my_id)
