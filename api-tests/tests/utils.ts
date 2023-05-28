import { GraphQLClient, gql } from 'graphql-request'
import { TokenCreateMutation } from '../generated/graphql'

// todo - przesunac do envow
const endpoint = import.meta.env.apiEndpoint

export const makeClient = (): GraphQLClient => new GraphQLClient(endpoint)

export const makeAuthorizedClient = async (): Promise<GraphQLClient> => {
  const client = makeClient()
  const mutation = gql`
    mutation TokenCreate($email: String!, $password: String!) {
      tokenCreate(email: $email, password: $password) {
        csrfToken
        refreshToken
        token
        errors: accountErrors {
          ...AccountError
        }
        user {
          id
          email
        }
      }
    }
    fragment AccountError on AccountError {
      code
      field
      message
    }
  `
  const result = await client.request<TokenCreateMutation>(mutation, {
    email: 'testers+dashboard@saleor.io',
    password: 'test1234',
  })
  return new GraphQLClient(endpoint, {
    headers: {
      Authorization: `bearer ${result.tokenCreate.token}`,
    },
  })
}
