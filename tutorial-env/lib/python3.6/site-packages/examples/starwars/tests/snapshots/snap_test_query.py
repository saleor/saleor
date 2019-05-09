# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["test_hero_name_query 1"] = {"data": {"hero": {"name": "R2-D2"}}}

snapshots["test_hero_name_and_friends_query 1"] = {
    "data": {
        "hero": {
            "id": "2001",
            "name": "R2-D2",
            "friends": [
                {"name": "Luke Skywalker"},
                {"name": "Han Solo"},
                {"name": "Leia Organa"},
            ],
        }
    }
}

snapshots["test_nested_query 1"] = {
    "data": {
        "hero": {
            "name": "R2-D2",
            "friends": [
                {
                    "name": "Luke Skywalker",
                    "appearsIn": ["NEWHOPE", "EMPIRE", "JEDI"],
                    "friends": [
                        {"name": "Han Solo"},
                        {"name": "Leia Organa"},
                        {"name": "C-3PO"},
                        {"name": "R2-D2"},
                    ],
                },
                {
                    "name": "Han Solo",
                    "appearsIn": ["NEWHOPE", "EMPIRE", "JEDI"],
                    "friends": [
                        {"name": "Luke Skywalker"},
                        {"name": "Leia Organa"},
                        {"name": "R2-D2"},
                    ],
                },
                {
                    "name": "Leia Organa",
                    "appearsIn": ["NEWHOPE", "EMPIRE", "JEDI"],
                    "friends": [
                        {"name": "Luke Skywalker"},
                        {"name": "Han Solo"},
                        {"name": "C-3PO"},
                        {"name": "R2-D2"},
                    ],
                },
            ],
        }
    }
}

snapshots["test_fetch_luke_query 1"] = {"data": {"human": {"name": "Luke Skywalker"}}}

snapshots["test_fetch_some_id_query 1"] = {
    "data": {"human": {"name": "Luke Skywalker"}}
}

snapshots["test_fetch_some_id_query2 1"] = {"data": {"human": {"name": "Han Solo"}}}

snapshots["test_invalid_id_query 1"] = {"data": {"human": None}}

snapshots["test_fetch_luke_aliased 1"] = {"data": {"luke": {"name": "Luke Skywalker"}}}

snapshots["test_fetch_luke_and_leia_aliased 1"] = {
    "data": {"luke": {"name": "Luke Skywalker"}, "leia": {"name": "Leia Organa"}}
}

snapshots["test_duplicate_fields 1"] = {
    "data": {
        "luke": {"name": "Luke Skywalker", "homePlanet": "Tatooine"},
        "leia": {"name": "Leia Organa", "homePlanet": "Alderaan"},
    }
}

snapshots["test_use_fragment 1"] = {
    "data": {
        "luke": {"name": "Luke Skywalker", "homePlanet": "Tatooine"},
        "leia": {"name": "Leia Organa", "homePlanet": "Alderaan"},
    }
}

snapshots["test_check_type_of_r2 1"] = {
    "data": {"hero": {"__typename": "Droid", "name": "R2-D2"}}
}

snapshots["test_check_type_of_luke 1"] = {
    "data": {"hero": {"__typename": "Human", "name": "Luke Skywalker"}}
}
