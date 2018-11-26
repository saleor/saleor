import * as React from "react";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";
import { TypedAttributeUpdateMutation } from "../mutations";
import {
  AttributeUpdate,
  AttributeUpdateVariables
} from "../types/AttributeUpdate";

interface AttributeUpdateProviderProps extends PartialMutationProviderProps {
  children: PartialMutationProviderRenderProps<
    AttributeUpdate,
    AttributeUpdateVariables
  >;
}

const AttributeUpdateProvider: React.StatelessComponent<
  AttributeUpdateProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedAttributeUpdateMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, loading, error }) => {
      return children({
        data,
        error,
        loading,
        mutate
      });
    }}
  </TypedAttributeUpdateMutation>
);

export default AttributeUpdateProvider;
