import * as React from "react";

import { TypedOrderDraftCancelMutation } from "../mutations";
import {
  OrderDraftCancel,
  OrderDraftCancelVariables
} from "../types/OrderDraftCancel";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";

interface OrderDraftCancelMutationProviderProps
  extends PartialMutationProviderProps<OrderDraftCancel> {
  children: PartialMutationProviderRenderProps<
    OrderDraftCancel,
    OrderDraftCancelVariables
  >;
}

const OrderDraftCancelMutationProvider: React.StatelessComponent<
  OrderDraftCancelMutationProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedOrderDraftCancelMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedOrderDraftCancelMutation>
);

export default OrderDraftCancelMutationProvider;
