import * as React from "react";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";
import {
  VerifyTokenMutation,
  VerifyTokenMutationVariables
} from "../../gql-types";
import { TypedVerifyTokenMutation } from "../mutations";

interface TokenVerifyProviderProps
  extends PartialMutationProviderProps<VerifyTokenMutation> {
  children: PartialMutationProviderRenderProps<
    VerifyTokenMutation,
    VerifyTokenMutationVariables
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

export default TokenVerifyProvider;
