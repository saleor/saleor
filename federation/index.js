const { ApolloServer } = require("apollo-server-fastify");
const { ApolloGateway } = require("@apollo/gateway");
const {
  ApolloServerPluginLandingPageGraphQLPlayground,
} = require("apollo-server-core");
const fastify = require("fastify");

const serviceList = [
  {
    name: "saleor",
    url: "https://w8-saleor-staging.herokuapp.com/graphql/",
  },
  // {
  //   name: "social-login",
  //   url: `https://w8-saleor-pr-${process.env.PR_NUMBER}.herokuapp.com/plugins/social-login/graphql`,
  // }
];

function fastifyAppClosePlugin(app) {
  return {
    async serverWillStart() {
      return {
        async drainServer() {
          await app.close();
        },
      };
    },
  };
}

const gateway = new ApolloGateway({ serviceList });
const app = fastify();
const server = new ApolloServer({
  gateway,
  plugins: [
    fastifyAppClosePlugin(app),
    ApolloServerPluginLandingPageGraphQLPlayground({
      httpServer: app.server,
    }),
  ],
});

app.get("/", (request, reply) => {
  reply.redirect("/graphql");
});
server
  .start()
  .then(() => app.register(server.createHandler()))
  .then(() => app.listen(process.env.PORT, '0.0.0.0'))
  .then(() => {
    const { port, address } = app.server.address();
    console.log(`🚀  Gateway is ready at http://${address}:${port}${server.graphqlPath}`);
  })
  .catch((err) => {
    console.error(err);
  });
