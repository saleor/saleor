import * as React from "react";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";
import { TypedVerifyTokenMutation } from "../mutations";
import { VerifyToken, VerifyTokenVariables } from "../types/VerifyToken";

interface TokenVerifyProviderProps
  extends PartialMutationProviderProps<VerifyToken> {
  children: PartialMutationProviderRenderProps<
    VerifyToken,
    VerifyTokenVariables
  >;
}

const TokenVerifyProvider: React.StatelessComponent<
  TokenVerifyProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedVerifyTokenMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { called, data, error, loading }) =>
      children({ called, data, error, loading, mutate })
    }
  </TypedVerifyTokenMutation>
);
TokenVerifyProvider.displayName = "TokenVerifyProvider";
export default TokenVerifyProvider;
