import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    include: [__dirname + '*/src/**/*.test.ts'],
  },
})
