import type { CodegenConfig } from '@graphql-codegen/cli'
import { baseUrl } from '~/utils'

const config: CodegenConfig = {
  schema: baseUrl,
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
