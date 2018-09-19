import * as React from "react";

import {
  OrderCancelMutation,
  OrderCancelMutationVariables
} from "../../gql-types";
import { TypedOrderCancelMutation } from "../mutations";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";

interface OrderCancelMutationProviderProps
  extends PartialMutationProviderProps<OrderCancelMutation> {
  children: PartialMutationProviderRenderProps<
    OrderCancelMutation,
    OrderCancelMutationVariables
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
