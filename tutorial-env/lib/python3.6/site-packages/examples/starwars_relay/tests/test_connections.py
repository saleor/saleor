from graphene.test import Client

from ..data import setup
from ..schema import schema

setup()

client = Client(schema)


def test_correct_fetch_first_ship_rebels(snapshot):
    query = """
    query RebelsShipsQuery {
      rebels {
        name,
        ships(first: 1) {
          pageInfo {
            startCursor
            endCursor
            hasNextPage
            hasPreviousPage
          }
          edges {
            cursor
            node {
              name
            }
          }
        }
      }
    }
    """
    snapshot.assert_match(client.execute(query))
