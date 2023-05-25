import { describe, expect, it } from 'vitest'
import { GraphQLClient } from 'graphql-request'

export const makeClient = (token: string): GraphQLClient => {
  const baseEndpoint = 'https://master.staging.saleor.cloud/dashboard'

  return new GraphQLClient(baseEndpoint, {
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
