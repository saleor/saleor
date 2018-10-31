import * as React from "react";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";
import { TypedAttributeDeleteMutation } from "../mutations";
import {
  AttributeDelete,
  AttributeDeleteVariables
} from "../types/AttributeDelete";

interface AttributeDeleteProviderProps extends PartialMutationProviderProps {
  children: PartialMutationProviderRenderProps<
    AttributeDelete,
    AttributeDeleteVariables
  >;
}

const AttributeDeleteProvider: React.StatelessComponent<
  AttributeDeleteProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedAttributeDeleteMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, loading, error }) => {
      return children({
        data,
        error,
        loading,
        mutate
      });
    }}
  </TypedAttributeDeleteMutation>
);

export default AttributeDeleteProvider;
