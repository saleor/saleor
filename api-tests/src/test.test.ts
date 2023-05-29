import { describe, expect, it } from 'vitest'
import { makeClient } from './utils'
import { gql } from 'graphql-request'
import { TokenCreateMutation } from '../generated/graphql'

describe('dummy test', () => {
  it('checks creating access tokens', async () => {
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
    expect(result.tokenCreate?.csrfToken).toBeDefined()
    expect(result.tokenCreate?.token).toBeDefined()
    expect(result.tokenCreate?.refreshToken).toBeDefined()
    expect(result.tokenCreate?.errors).toHaveLength(0)
  })
})
