from graphene.test import Client

from ..data import setup
from ..schema import schema

setup()

client = Client(schema)


def test_str_schema(snapshot):
    snapshot.assert_match(str(schema))


def test_correctly_fetches_id_name_rebels(snapshot):
    query = """
      query RebelsQuery {
        rebels {
          id
          name
        }
      }
    """
    snapshot.assert_match(client.execute(query))


def test_correctly_refetches_rebels(snapshot):
    query = """
      query RebelsRefetchQuery {
        node(id: "RmFjdGlvbjox") {
          id
          ... on Faction {
            name
          }
        }
      }
    """
    snapshot.assert_match(client.execute(query))


def test_correctly_fetches_id_name_empire(snapshot):
    query = """
      query EmpireQuery {
        empire {
          id
          name
        }
      }
    """
    snapshot.assert_match(client.execute(query))


def test_correctly_refetches_empire(snapshot):
    query = """
      query EmpireRefetchQuery {
        node(id: "RmFjdGlvbjoy") {
          id
          ... on Faction {
            name
          }
        }
      }
    """
    snapshot.assert_match(client.execute(query))


def test_correctly_refetches_xwing(snapshot):
    query = """
      query XWingRefetchQuery {
        node(id: "U2hpcDox") {
          id
          ... on Ship {
            name
          }
        }
      }
    """
    snapshot.assert_match(client.execute(query))
