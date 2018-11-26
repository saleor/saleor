import * as React from "react";

import { TypedOrderCancelMutation } from "../mutations";
import { OrderCancel, OrderCancelVariables } from "../types/OrderCancel";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";

interface OrderCancelMutationProviderProps
  extends PartialMutationProviderProps<OrderCancel> {
  children: PartialMutationProviderRenderProps<
    OrderCancel,
    OrderCancelVariables
  >;
}

const OrderCancelMutationProvider: React.StatelessComponent<
  OrderCancelMutationProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedOrderCancelMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedOrderCancelMutation>
);

export default OrderCancelMutationProvider;
