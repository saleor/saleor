# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["test_correctly_fetches_id_name_rebels 1"] = {
    "data": {
        "rebels": {"id": "RmFjdGlvbjox", "name": "Alliance to Restore the Republic"}
    }
}

snapshots["test_correctly_refetches_rebels 1"] = {
    "data": {"node": {"id": "RmFjdGlvbjox", "name": "Alliance to Restore the Republic"}}
}

snapshots["test_correctly_fetches_id_name_empire 1"] = {
    "data": {"empire": {"id": "RmFjdGlvbjoy", "name": "Galactic Empire"}}
}

snapshots["test_correctly_refetches_empire 1"] = {
    "data": {"node": {"id": "RmFjdGlvbjoy", "name": "Galactic Empire"}}
}

snapshots["test_correctly_refetches_xwing 1"] = {
    "data": {"node": {"id": "U2hpcDox", "name": "X-Wing"}}
}

snapshots[
    "test_str_schema 1"
] = """schema {
  query: Query
  mutation: Mutation
}

type Faction implements Node {
  id: ID!
  name: String
  ships(before: String, after: String, first: Int, last: Int): ShipConnection
}

input IntroduceShipInput {
  shipName: String!
  factionId: String!
  clientMutationId: String
}

type IntroduceShipPayload {
  ship: Ship
  faction: Faction
  clientMutationId: String
}

type Mutation {
  introduceShip(input: IntroduceShipInput!): IntroduceShipPayload
}

interface Node {
  id: ID!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

type Query {
  rebels: Faction
  empire: Faction
  node(id: ID!): Node
}

type Ship implements Node {
  id: ID!
  name: String
}

type ShipConnection {
  pageInfo: PageInfo!
  edges: [ShipEdge]!
}

type ShipEdge {
  node: Ship
  cursor: String!
}
"""
