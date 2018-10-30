import * as React from "react";

import { TypedOrderVoidMutation } from "../mutations";
import { OrderVoid, OrderVoidVariables } from "../types/OrderVoid";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";

interface OrderVoidMutationProviderProps
  extends PartialMutationProviderProps<OrderVoid> {
  children: PartialMutationProviderRenderProps<
    OrderVoid,
    OrderVoidVariables
  >;
}

const OrderVoidMutationProvider: React.StatelessComponent<
  OrderVoidMutationProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedOrderVoidMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedOrderVoidMutation>
);

export default OrderVoidMutationProvider;
