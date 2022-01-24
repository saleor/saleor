const { ApolloServer } = require('apollo-server-express');
const { ApolloServerPluginDrainHttpServer, ApolloServerPluginLandingPageGraphQLPlayground } = require('apollo-server-core');
const express = require('express');
const http = require('http');
const { ApolloGateway } = require("@apollo/gateway");

const serviceList = [
  {
    name: "saleor",
    url: "https://w8-saleor-staging.herokuapp.com/graphql/",
  },
  {
    name: "otp",
    url: `https://w8-saleor-pr-${process.env.PR_NUMBER}.herokuapp.com/plugins/otp/graphql`,
  },
  {
    name: "social-login",
    url: "https://w8-saleor-staging.herokuapp.com/plugins/social-login/",
  },
  // {
  //   name: "plugin-id",
  //   url: `https://w8-saleor-pr-${process.env.PR_NUMBER}.herokuapp.com/plugins/PLUGIN-ID/graphql`,
  // }
];


async function startApolloServer(typeDefs, resolvers) {
  const gateway = new ApolloGateway({ serviceList });
  const app = express();
  const httpServer = http.createServer(app);
  const server = new ApolloServer({
    gateway,
    plugins: [
      ApolloServerPluginDrainHttpServer({ httpServer }),
      ApolloServerPluginLandingPageGraphQLPlayground({
        httpServer: httpServer,
      }),
    ],
  });

  await server.start();
  server.applyMiddleware({ app });
  await new Promise(resolve => httpServer.listen({ port: process.env.PORT || 4000 }, resolve));
  console.log(`🚀 Server ready at http://localhost:4000${server.graphqlPath}`);
}

startApolloServer()
