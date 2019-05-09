Relay Library for GraphQL Python
================================

This is a library to allow the easy creation of Relay-compliant servers
using the `GraphQL
Python <https://github.com/graphql-python/graphql-core>`__ reference
implementation of a GraphQL server.

Note: The code is a **exact** port of the original `graphql-relay js
implementation <https://github.com/graphql/graphql-relay-js>`__ from
Facebook

|PyPI version| |Build Status| |Coverage Status|

Getting Started
---------------

A basic understanding of GraphQL and of the GraphQL Python
implementation is needed to provide context for this library.

An overview of GraphQL in general is available in the
`README <https://github.com/graphql-python/graphql-core/blob/master/README.md>`__
for the `Specification for
GraphQL <https://github.com/graphql-python/graphql-core>`__.

This library is designed to work with the the `GraphQL
Python <https://github.com/graphql-python/graphql-core>`__ reference
implementation of a GraphQL server.

An overview of the functionality that a Relay-compliant GraphQL server
should provide is in the `GraphQL Relay
Specification <https://facebook.github.io/relay/docs/graphql-relay-specification.html>`__
on the `Relay website <https://facebook.github.io/relay/>`__. That
overview describes a simple set of examples that exist as
`tests <tests>`__ in this repository. A good way to get started with
this repository is to walk through that documentation and the
corresponding tests in this library together.

Using Relay Library for GraphQL Python (graphql-core)
-----------------------------------------------------

Install Relay Library for GraphQL Python

.. code:: sh

    pip install graphql-core --pre # Last version of graphql-core
    pip install graphql-relay

When building a schema for
`GraphQL <https://github.com/graphql-python/graphql-core>`__, the
provided library functions can be used to simplify the creation of Relay
patterns.

Connections
~~~~~~~~~~~

Helper functions are provided for both building the GraphQL types for
connections and for implementing the ``resolver`` method for fields
returning those types.

-  ``connection_args`` returns the arguments that fields should provide
   when they return a connection type.
-  ``connection_definitions`` returns a ``connection_type`` and its
   associated ``edgeType``, given a name and a node type.
-  ``connection_from_list`` is a helper method that takes an array and
   the arguments from ``connection_args``, does pagination and
   filtering, and returns an object in the shape expected by a
   ``connection_type``'s ``resolver`` function.
-  ``connection_from_promised_list`` is similar to
   ``connection_from_list``, but it takes a promise that resolves to an
   array, and returns a promise that resolves to the expected shape by
   ``connection_type``.
-  ``cursor_for_object_in_connection`` is a helper method that takes an
   array and a member object, and returns a cursor for use in the
   mutation payload.

An example usage of these methods from the `test
schema <tests/starwars/schema.py>`__:

.. code:: python

    ship_edge, ship_connection = connection_definitions('Ship', shipType)

    factionType = GraphQLObjectType(
        name= 'Faction',
        description= 'A faction in the Star Wars saga',
        fields= lambda: {
            'id': global_id_field('Faction'),
            'name': GraphQLField(
                GraphQLString,
                description='The name of the faction.',
            ),
            'ships': GraphQLField(
                shipConnection,
                description= 'The ships used by the faction.',
                args= connection_args,
                resolver= lambda faction, args, *_: connection_from_list(
                    map(getShip, faction.ships),
                    args
                ),
            )
        },
        interfaces= [node_interface]
    )

This shows adding a ``ships`` field to the ``Faction`` object that is a
connection. It uses
``connection_definitions({name: 'Ship', nodeType: shipType})`` to create
the connection type, adds ``connection_args`` as arguments on this
function, and then implements the resolver function by passing the array
of ships and the arguments to ``connection_from_list``.

Object Identification
~~~~~~~~~~~~~~~~~~~~~

Helper functions are provided for both building the GraphQL types for
nodes and for implementing global IDs around local IDs.

-  ``node_definitions`` returns the ``Node`` interface that objects can
   implement, and returns the ``node`` root field to include on the
   query type. To implement this, it takes a function to resolve an ID
   to an object, and to determine the type of a given object.
-  ``to_global_id`` takes a type name and an ID specific to that type
   name, and returns a "global ID" that is unique among all types.
-  ``from_global_id`` takes the "global ID" created by ``toGlobalID``,
   and retuns the type name and ID used to create it.
-  ``global_id_field`` creates the configuration for an ``id`` field on
   a node.
-  ``plural_identifying_root_field`` creates a field that accepts a list
   of non-ID identifiers (like a username) and maps then to their
   corresponding objects.

An example usage of these methods from the `test
schema <tests/starwars/schema.py>`__:

.. code:: python

    def get_node(global_id, context, info):
        resolvedGlobalId = from_global_id(global_id)
        _type, _id = resolvedGlobalId.type, resolvedGlobalId.id
        if _type == 'Faction':
            return getFaction(_id)
        elif _type == 'Ship':
            return getShip(_id)
        else:
            return None

    def get_node_type(obj, context, info):
        if isinstance(obj, Faction):
            return factionType
        else:
            return shipType

    node_interface, node_field = node_definitions(get_node, get_node_type)

    factionType = GraphQLObjectType(
        name= 'Faction',
        description= 'A faction in the Star Wars saga',
        fields= lambda: {
            'id': global_id_field('Faction'),
        },
        interfaces= [node_interface]
    )

    queryType = GraphQLObjectType(
        name= 'Query',
        fields= lambda: {
            'node': node_field
        }
    )

This uses ``node_definitions`` to construct the ``Node`` interface and
the ``node`` field; it uses ``from_global_id`` to resolve the IDs passed
in in the implementation of the function mapping ID to object. It then
uses the ``global_id_field`` method to create the ``id`` field on
``Faction``, which also ensures implements the ``node_interface``.
Finally, it adds the ``node`` field to the query type, using the
``node_field`` returned by ``node_definitions``.

Mutations
~~~~~~~~~

A helper function is provided for building mutations with single inputs
and client mutation IDs.

-  ``mutation_with_client_mutation_id`` takes a name, input fields,
   output fields, and a mutation method to map from the input fields to
   the output fields, performing the mutation along the way. It then
   creates and returns a field configuration that can be used as a
   top-level field on the mutation type.

An example usage of these methods from the `test
schema <tests/starwars/schema.py>`__:

.. code:: python

    class IntroduceShipMutation(object):
        def __init__(self, shipId, factionId, clientMutationId=None):
            self.shipId = shipId
            self.factionId = factionId
            self.clientMutationId = None

    def mutate_and_get_payload(data, *_):
        shipName = data.get('shipName')
        factionId = data.get('factionId')
        newShip = createShip(shipName, factionId)
        return IntroduceShipMutation(
            shipId=newShip.id,
            factionId=factionId,
        )

    shipMutation = mutation_with_client_mutation_id(
        'IntroduceShip',
        input_fields={
            'shipName': GraphQLField(
                GraphQLNonNull(GraphQLString)
            ),
            'factionId': GraphQLField(
                GraphQLNonNull(GraphQLID)
            )
        },
        output_fields= {
            'ship': GraphQLField(
                shipType,
                resolver= lambda payload, *_: getShip(payload.shipId)
            ),
            'faction': GraphQLField(
                factionType,
                resolver= lambda payload, *_: getFaction(payload.factionId)
            )
        },
        mutate_and_get_payload=mutate_and_get_payload
    )

    mutationType = GraphQLObjectType(
        'Mutation',
        fields= lambda: {
            'introduceShip': shipMutation
        }
    )

This code creates a mutation named ``IntroduceShip``, which takes a
faction ID and a ship name as input. It outputs the ``Faction`` and the
``Ship`` in question. ``mutate_and_get_payload`` then gets an object
with a property for each input field, performs the mutation by
constructing the new ship, then returns an object that will be resolved
by the output fields.

Our mutation type then creates the ``introduceShip`` field using the
return value of ``mutation_with_client_mutation_id``.

Contributing
------------

After cloning this repo, ensure dependencies are installed by running:

.. code:: sh

    python setup.py install

After developing, the full test suite can be evaluated by running:

.. code:: sh

    python setup.py test # Use --pytest-args="-v -s" for verbose mode

.. |PyPI version| image:: https://badge.fury.io/py/graphql-relay.svg
   :target: https://badge.fury.io/py/graphql-relay
.. |Build Status| image:: https://travis-ci.org/graphql-python/graphql-relay-py.svg?branch=master
   :target: https://travis-ci.org/graphql-python/graphql-relay-py
.. |Coverage Status| image:: https://coveralls.io/repos/graphql-python/graphql-relay-py/badge.svg?branch=master&service=github
   :target: https://coveralls.io/github/graphql-python/graphql-relay-py?branch=master


