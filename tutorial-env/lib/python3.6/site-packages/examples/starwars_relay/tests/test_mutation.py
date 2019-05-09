from graphene.test import Client

from ..data import setup
from ..schema import schema

setup()

client = Client(schema)


def test_mutations(snapshot):
    query = """
    mutation MyMutation {
      introduceShip(input:{clientMutationId:"abc", shipName: "Peter", factionId: "1"}) {
        ship {
          id
          name
        }
        faction {
          name
          ships {
            edges {
              node {
                id
                name
              }
            }
          }
        }
      }
    }
    """
    snapshot.assert_match(client.execute(query))
