import { GraphQLClient, gql } from 'graphql-request'
import { TokenCreateMutation } from '../generated/graphql'

export const baseUrl: string = import.meta.env.apiEndpoint

export const makeClient = (): GraphQLClient => new GraphQLClient(baseUrl)

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
  return new GraphQLClient(baseUrl, {
    headers: {
      Authorization: `bearer ${result.tokenCreate?.token}`,
    },
  })
}
