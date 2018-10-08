import * as React from "react";

import { TypedOrderFulfillmentUpdateTrackingMutation } from "../mutations";
import {
  OrderFulfillmentUpdateTracking,
  OrderFulfillmentUpdateTrackingVariables
} from "../types/OrderFulfillmentUpdateTracking";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";

interface OrderFulfillmentUpdateTrackingProviderProps
  extends PartialMutationProviderProps<OrderFulfillmentUpdateTracking> {
  children: PartialMutationProviderRenderProps<
    OrderFulfillmentUpdateTracking,
    OrderFulfillmentUpdateTrackingVariables
  >;
}

const OrderFulfillmentUpdateTrackingProvider: React.StatelessComponent<
  OrderFulfillmentUpdateTrackingProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedOrderFulfillmentUpdateTrackingMutation
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
  </TypedOrderFulfillmentUpdateTrackingMutation>
);

export default OrderFulfillmentUpdateTrackingProvider;
