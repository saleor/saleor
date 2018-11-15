import * as React from "react";

import { TypedOrderLineDeleteMutation } from "../mutations";
import {
  OrderLineDelete,
  OrderLineDeleteVariables
} from "../types/OrderLineDelete";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";

interface OrderLineDeleteProviderProps
  extends PartialMutationProviderProps<OrderLineDelete> {
  children: PartialMutationProviderRenderProps<
    OrderLineDelete,
    OrderLineDeleteVariables
  >;
}

const OrderLineDeleteProvider: React.StatelessComponent<
  OrderLineDeleteProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedOrderLineDeleteMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedOrderLineDeleteMutation>
);

export default OrderLineDeleteProvider;
