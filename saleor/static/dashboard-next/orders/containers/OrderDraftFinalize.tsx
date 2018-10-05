import * as React from "react";

import { TypedOrderDraftFinalizeMutation } from "../mutations";
import {
  OrderDraftFinalize,
  OrderDraftFinalizeVariables
} from "../types/OrderDraftFinalize";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";

interface OrderDraftFinalizeMutationProviderProps
  extends PartialMutationProviderProps<OrderDraftFinalize> {
  children: PartialMutationProviderRenderProps<
    OrderDraftFinalize,
    OrderDraftFinalizeVariables
  >;
}

const OrderDraftFinalizeMutationProvider: React.StatelessComponent<
  OrderDraftFinalizeMutationProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedOrderDraftFinalizeMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedOrderDraftFinalizeMutation>
);

export default OrderDraftFinalizeMutationProvider;
