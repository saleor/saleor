import { describe, expect, it } from 'vitest'
import { GraphQLClient, gql } from 'graphql-request'

export const registerUser = gql`
  mutation {
    accountRegister(
      input: { email: "customer@example.com", password: "secret", channel: "default-channel" }
    ) {
      errors {
        field
        code
      }
      user {
        email
        isActive
        userPermissions
      }
    }
  }
`
export const makeClient = (token: string): GraphQLClient => {
  const endpoint = 'https://api.github.com/graphql'

  return new GraphQLClient(endpoint, {
    headers: {
      Authorization: `bearer ${token}`,
    },
  })
}

describe('1st test', () => {
  it('tests something', () => {
    expect(true).toBe(true)
  })
})
