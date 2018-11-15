import * as React from "react";

import { TypedOrderDraftUpdateMutation } from "../mutations";
import {
  OrderDraftUpdate,
  OrderDraftUpdateVariables
} from "../types/OrderDraftUpdate";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";

interface OrderDraftUpdateProviderProps
  extends PartialMutationProviderProps<OrderDraftUpdate> {
  children: PartialMutationProviderRenderProps<
    OrderDraftUpdate,
    OrderDraftUpdateVariables
  >;
}

const OrderDraftUpdateProvider: React.StatelessComponent<
  OrderDraftUpdateProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedOrderDraftUpdateMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedOrderDraftUpdateMutation>
);

export default OrderDraftUpdateProvider;
