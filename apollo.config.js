module.exports = {
  client: {
    addTypename: true,
    includes: [
      'saleor/static/dashboard-next/**/*.ts',
      'saleor/static/dashboard-next/**/*.tsx'
    ],
    name: 'storefront',
    service: {
      localSchemaFile: 'saleor/graphql/schema.graphql',
      name: 'saleor'
    }
  }
};
