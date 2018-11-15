import * as React from "react";

import { TypedOrderLineAddMutation } from "../mutations";
import { OrderLineAdd, OrderLineAddVariables } from "../types/OrderLineAdd";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";

interface OrderLineAddProviderProps
  extends PartialMutationProviderProps<OrderLineAdd> {
  children: PartialMutationProviderRenderProps<
    OrderLineAdd,
    OrderLineAddVariables
  >;
}

const OrderLineAddProvider: React.StatelessComponent<
  OrderLineAddProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedOrderLineAddMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedOrderLineAddMutation>
);

export default OrderLineAddProvider;
