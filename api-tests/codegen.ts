import type { CodegenConfig } from '@graphql-codegen/cli'

const config: CodegenConfig = {
  schema: 'https://master.staging.saleor.cloud/graphql/',
  documents: ['tests/**/*.ts'],
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
