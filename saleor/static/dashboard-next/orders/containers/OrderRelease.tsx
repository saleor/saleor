import * as React from "react";

import {
  OrderReleaseMutation,
  OrderReleaseMutationVariables
} from "../../gql-types";
import { TypedOrderReleaseMutation } from "../mutations";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";

interface OrderReleaseMutationProviderProps
  extends PartialMutationProviderProps<OrderReleaseMutation> {
  children: PartialMutationProviderRenderProps<
    OrderReleaseMutation,
    OrderReleaseMutationVariables
  >;
}

const OrderReleaseMutationProvider: React.StatelessComponent<
  OrderReleaseMutationProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedOrderReleaseMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedOrderReleaseMutation>
);

export default OrderReleaseMutationProvider;
