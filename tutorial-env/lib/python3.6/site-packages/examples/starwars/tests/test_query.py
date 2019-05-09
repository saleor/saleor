from graphene.test import Client

from ..data import setup
from ..schema import schema

setup()

client = Client(schema)


def test_hero_name_query(snapshot):
    query = """
        query HeroNameQuery {
          hero {
            name
          }
        }
    """
    snapshot.assert_match(client.execute(query))


def test_hero_name_and_friends_query(snapshot):
    query = """
        query HeroNameAndFriendsQuery {
          hero {
            id
            name
            friends {
              name
            }
          }
        }
    """
    snapshot.assert_match(client.execute(query))


def test_nested_query(snapshot):
    query = """
        query NestedQuery {
          hero {
            name
            friends {
              name
              appearsIn
              friends {
                name
              }
            }
          }
        }
    """
    snapshot.assert_match(client.execute(query))


def test_fetch_luke_query(snapshot):
    query = """
        query FetchLukeQuery {
          human(id: "1000") {
            name
          }
        }
    """
    snapshot.assert_match(client.execute(query))


def test_fetch_some_id_query(snapshot):
    query = """
        query FetchSomeIDQuery($someId: String!) {
          human(id: $someId) {
            name
          }
        }
    """
    params = {"someId": "1000"}
    snapshot.assert_match(client.execute(query, variable_values=params))


def test_fetch_some_id_query2(snapshot):
    query = """
        query FetchSomeIDQuery($someId: String!) {
          human(id: $someId) {
            name
          }
        }
    """
    params = {"someId": "1002"}
    snapshot.assert_match(client.execute(query, variable_values=params))


def test_invalid_id_query(snapshot):
    query = """
        query humanQuery($id: String!) {
          human(id: $id) {
            name
          }
        }
    """
    params = {"id": "not a valid id"}
    snapshot.assert_match(client.execute(query, variable_values=params))


def test_fetch_luke_aliased(snapshot):
    query = """
        query FetchLukeAliased {
          luke: human(id: "1000") {
            name
          }
        }
    """
    snapshot.assert_match(client.execute(query))


def test_fetch_luke_and_leia_aliased(snapshot):
    query = """
        query FetchLukeAndLeiaAliased {
          luke: human(id: "1000") {
            name
          }
          leia: human(id: "1003") {
            name
          }
        }
    """
    snapshot.assert_match(client.execute(query))


def test_duplicate_fields(snapshot):
    query = """
        query DuplicateFields {
          luke: human(id: "1000") {
            name
            homePlanet
          }
          leia: human(id: "1003") {
            name
            homePlanet
          }
        }
    """
    snapshot.assert_match(client.execute(query))


def test_use_fragment(snapshot):
    query = """
        query UseFragment {
          luke: human(id: "1000") {
            ...HumanFragment
          }
          leia: human(id: "1003") {
            ...HumanFragment
          }
        }
        fragment HumanFragment on Human {
          name
          homePlanet
        }
    """
    snapshot.assert_match(client.execute(query))


def test_check_type_of_r2(snapshot):
    query = """
        query CheckTypeOfR2 {
          hero {
            __typename
            name
          }
        }
    """
    snapshot.assert_match(client.execute(query))


def test_check_type_of_luke(snapshot):
    query = """
        query CheckTypeOfLuke {
          hero(episode: EMPIRE) {
            __typename
            name
          }
        }
    """
    snapshot.assert_match(client.execute(query))
