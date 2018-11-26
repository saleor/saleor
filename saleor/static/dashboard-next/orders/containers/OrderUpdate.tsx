import * as React from "react";

import { TypedOrderUpdateMutation } from "../mutations";
import { OrderUpdate, OrderUpdateVariables } from "../types/OrderUpdate";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";

interface OrderUpdateProviderProps
  extends PartialMutationProviderProps<OrderUpdate> {
  children: PartialMutationProviderRenderProps<
    OrderUpdate,
    OrderUpdateVariables
  >;
}

const OrderUpdateProvider: React.StatelessComponent<
  OrderUpdateProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedOrderUpdateMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedOrderUpdateMutation>
);

export default OrderUpdateProvider;
