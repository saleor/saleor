import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    include: ['src/**/*.test.{ts,tsx}'],
    env: {
      apiEndpoint: 'https://master.staging.saleor.cloud/graphql/',
    },
  },
  define: {
    admin: {
      email: 'testers+dashboard@saleor.io',
      password: 'test1234',
    },
  },
})
