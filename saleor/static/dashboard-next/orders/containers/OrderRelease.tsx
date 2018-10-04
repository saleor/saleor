import * as React from "react";

import { TypedOrderReleaseMutation } from "../mutations";
import { OrderRelease, OrderReleaseVariables } from "../types/OrderRelease";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";

interface OrderReleaseMutationProviderProps
  extends PartialMutationProviderProps<OrderRelease> {
  children: PartialMutationProviderRenderProps<
    OrderRelease,
    OrderReleaseVariables
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
