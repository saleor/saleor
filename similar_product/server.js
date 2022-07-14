
/*  GraphQL interface build (Product and Item Types) for getting 
    query request (inside similar_products folder named as query.graphql) 
    to run application abd run following schemas */

const express = require('express');
const expressGraphQL = require('express-graphql').graphqlHTTP;
const {
    GraphQLSchema, 
    GraphQLObjectType,
    GraphQLString,
    GraphQLList,
    GraphQLScalarType,
    GraphQLInt, 
    GraphQLNonNull
} = require('graphql')

const app = express()

const ProductType = new GraphQLObjectType({                                              //   Product to query about (id and name)
    name: 'product',
    description: 'Attributes of product items',
    fields: () => ({
        productId: { type: GraphQLNonNull(GraphQLInt) },
        name: { type: GraphQLNonNull(GraphQLString) },
        itemId: { type: GraphQLNonNull(GraphQLInt) },
        item: {
            type: ItemType,
            resolve: (product) => {
                return items.find(item => item.productId === product.itemId)
            }
        }
    })
})

const ItemType = new GraphQLObjectType({                                              //   Similar Items relating to product 
    name: 'item',
    description: 'Similar Items',
    fields: () => ({
        itemId: { type: GraphQLNonNull(GraphQLInt) },
        name: { type: GraphQLNonNull(GraphQLString) },
        products: {type: new GraphQLList(ProductType),
            resolve: (item) =>{
                return products.filter(product => product.itemId === item.productId) 
             }
        }
    })
})

const RootQueryType = new GraphQLObjectType({                                                // Root query 
        name: 'Query',
        description: 'Root Query', 
        fields: () => ({
            product: {                                                                      // One particular product 
                type: ProductType,
                description: 'product',
                args: {
                    id: { type: GraphQLInt }
                },
                resolve: (parent, args ) => products.find(product => product.productId === args.id)
            },
            products: {                                                                     // List of products
                type: new GraphQLList(ProductType),
                description: 'List of all products',
                resolve: () => products  
            },
            items: {                                                                        // List of items
                type: new GraphQLList(ItemType),
                description: 'List of all items',
                resolve: () => items  
            },
            item: {                                                                         // One particular item
                type: ItemType,
                description: 'item',
                args:{
                    id: { type: GraphQLInt }
                },
                resolve: (parent, args) => items.find(item => item.itemId === args.id)
            }
      })
})

const schema = new GraphQLSchema({
    query: RootQueryType
})

app.use('/graphql', expressGraphQL({
    schema: schema,
    graphiql: true  

}))
app.listen(5000., () => console.log('Server Running'))


