import * as React from "react";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";
import { TypedAttributeCreateMutation } from "../mutations";
import {
  AttributeCreate,
  AttributeCreateVariables
} from "../types/AttributeCreate";

interface AttributeCreateProviderProps extends PartialMutationProviderProps {
  children: PartialMutationProviderRenderProps<
    AttributeCreate,
    AttributeCreateVariables
  >;
}

const AttributeCreateProvider: React.StatelessComponent<
  AttributeCreateProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedAttributeCreateMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, loading, error }) => {
      return children({
        data,
        error,
        loading,
        mutate
      });
    }}
  </TypedAttributeCreateMutation>
);

export default AttributeCreateProvider;
