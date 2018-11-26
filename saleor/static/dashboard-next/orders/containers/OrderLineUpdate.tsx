import * as React from "react";

import { TypedOrderLineUpdateMutation } from "../mutations";
import {
  OrderLineUpdate,
  OrderLineUpdateVariables
} from "../types/OrderLineUpdate";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";

interface OrderLineUpdateProviderProps
  extends PartialMutationProviderProps<OrderLineUpdate> {
  children: PartialMutationProviderRenderProps<
    OrderLineUpdate,
    OrderLineUpdateVariables
  >;
}

const OrderLineUpdateProvider: React.StatelessComponent<
  OrderLineUpdateProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedOrderLineUpdateMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedOrderLineUpdateMutation>
);

export default OrderLineUpdateProvider;
