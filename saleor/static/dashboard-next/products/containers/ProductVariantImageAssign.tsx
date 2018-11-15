import * as React from "react";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";
import { TypedVariantImageAssignMutation } from "../mutations";
import {
  VariantImageAssign,
  VariantImageAssignVariables
} from "../types/VariantImageAssign";

interface VariantImageAssignProviderProps extends PartialMutationProviderProps {
  children: PartialMutationProviderRenderProps<
    VariantImageAssign,
    VariantImageAssignVariables
  >;
}

const VariantImageAssignProvider: React.StatelessComponent<
  VariantImageAssignProviderProps
> = ({ children, onError, onSuccess }) => (
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
