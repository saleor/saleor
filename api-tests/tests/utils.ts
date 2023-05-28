import { GraphQLClient, gql } from 'graphql-request'

export const makeClient = (): GraphQLClient => {
  // todo - przesunac do envow
  const endpoint = 'https://master.staging.saleor.cloud/graphql/'

  return new GraphQLClient(endpoint)
}

// export const makeClient = (token: string): GraphQLClient => {
//   const endpoint = 'https://master.staging.saleor.cloud/graphql'
//
//   return new GraphQLClient(endpoint, {
//     headers: {
//       Authorization: `bearer ${token}`,
//     },
//   })
// }
