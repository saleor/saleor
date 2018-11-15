import * as React from "react";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";
import { TypedVariantDeleteMutation } from "../mutations";
import { VariantDelete, VariantDeleteVariables } from "../types/VariantDelete";

interface VariantDeleteProviderProps extends PartialMutationProviderProps {
  id: string;
  children: PartialMutationProviderRenderProps<
    VariantDelete,
    VariantDeleteVariables
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
