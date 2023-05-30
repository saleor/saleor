import { defineConfig } from 'vitest/config'

const apiEndpoint = process.env.SCHEMA_URL

if (!apiEndpoint) {
  throw new Error('Missing SCHEMA_URL environment variable')
}

export default defineConfig({
  test: {
    include: ['src/**/*.test.{ts,tsx}'],
    env: {
      apiEndpoint,
    },
    setupFiles: ['dotenv/config'],
  },
})
