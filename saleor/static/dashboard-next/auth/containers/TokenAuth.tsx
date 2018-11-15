import * as React from "react";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";
import { TypedTokenAuthMutation } from "../mutations";
import { TokenAuth, TokenAuthVariables } from "../types/TokenAuth";

interface TokenAuthProviderProps
  extends PartialMutationProviderProps<TokenAuth> {
  children: PartialMutationProviderRenderProps<TokenAuth, TokenAuthVariables>;
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
TokenAuthProvider.displayName = "TokenAuthProvider";
export default TokenAuthProvider;
