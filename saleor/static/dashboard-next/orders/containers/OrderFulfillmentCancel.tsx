import * as React from "react";

import { TypedOrderFulfillmentCancelMutation } from "../mutations";
import {
  OrderFulfillmentCancel,
  OrderFulfillmentCancelVariables
} from "../types/OrderFulfillmentCancel";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";

interface OrderFulfillmentCancelProviderProps
  extends PartialMutationProviderProps<OrderFulfillmentCancel> {
  children: PartialMutationProviderRenderProps<
    OrderFulfillmentCancel,
    OrderFulfillmentCancelVariables
  >;
}

const OrderFulfillmentCancelProvider: React.StatelessComponent<
  OrderFulfillmentCancelProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedOrderFulfillmentCancelMutation
    onCompleted={onSuccess}
    onError={onError}
  >
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedOrderFulfillmentCancelMutation>
);

export default OrderFulfillmentCancelProvider;
