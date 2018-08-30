import * as React from "react";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";
import {
  VariantImageAssignMutation,
  VariantImageAssignMutationVariables
} from "../../gql-types";
import { TypedVariantImageAssignMutation } from "../mutations";

interface VariantImageAssignProviderProps extends PartialMutationProviderProps {
  id: string;
  children: PartialMutationProviderRenderProps<
    VariantImageAssignMutation,
    VariantImageAssignMutationVariables
  >;
}

const VariantImageAssignProvider: React.StatelessComponent<
  VariantImageAssignProviderProps
> = ({ id, children, onError, onSuccess }) => (
  <TypedVariantImageAssignMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, loading, error }) => {
      return children({
        data,
        error,
        loading,
        mutate
      });
    }}
  </TypedVariantImageAssignMutation>
);

export default VariantImageAssignProvider;
