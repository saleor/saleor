import * as React from "react";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";
import {
  VariantDeleteMutation,
  VariantDeleteMutationVariables
} from "../../gql-types";
import { TypedVariantDeleteMutation } from "../mutations";

interface VariantDeleteProviderProps extends PartialMutationProviderProps {
  id: string;
  children: PartialMutationProviderRenderProps<
    VariantDeleteMutation,
    VariantDeleteMutationVariables
  >;
}

const VariantDeleteProvider: React.StatelessComponent<
  VariantDeleteProviderProps
> = ({ id, children, onError, onSuccess }) => (
  <TypedVariantDeleteMutation
    variables={{ id }}
    onCompleted={onSuccess}
    onError={onError}
  >
    {(mutate, { data, loading, error }) => {
      return children({
        data,
        error,
        loading,
        mutate
      });
    }}
  </TypedVariantDeleteMutation>
);

export default VariantDeleteProvider;
