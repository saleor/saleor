import type { CodegenConfig } from '@graphql-codegen/cli'

const schemaUrl = process.env.SCHEMA_URL

if (!schemaUrl) {
  throw new Error('Missing SCHEMA_URL environment variable')
}

const config: CodegenConfig = {
  schema: schemaUrl,
  documents: ['src/**/*.ts'],
  config: { addExplicitOverride: true },
  generates: {
    './generated/': {
      preset: 'client',
      presetConfig: {
        gqlTagName: 'gql',
      },
    },
  },
}

export default config
