import * as React from "react";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";
import { TokenAuthMutation, TokenAuthMutationVariables } from "../../gql-types";
import { TypedTokenAuthMutation } from "../mutations";

interface TokenAuthProviderProps
  extends PartialMutationProviderProps<TokenAuthMutation> {
  children: PartialMutationProviderRenderProps<
    TokenAuthMutation,
    TokenAuthMutationVariables
  >;
}

const TokenAuthProvider: React.StatelessComponent<TokenAuthProviderProps> = ({
  children,
  onError,
  onSuccess
}) => (
  <TypedTokenAuthMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { called, data, error, loading }) =>
      children({ called, data, error, loading, mutate })
    }
  </TypedTokenAuthMutation>
);

export default TokenAuthProvider;
