import * as React from "react";

import { TypedOrderCreateFulfillmentMutation } from "../mutations";
import {
  OrderCreateFulfillment,
  OrderCreateFulfillmentVariables
} from "../types/OrderCreateFulfillment";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";

interface OrderCreateFulfillmentProviderProps
  extends PartialMutationProviderProps<OrderCreateFulfillment> {
  id: string;
  children: PartialMutationProviderRenderProps<
    OrderCreateFulfillment,
    OrderCreateFulfillmentVariables
  >;
}

const OrderCreateFulfillmentProvider: React.StatelessComponent<
  OrderCreateFulfillmentProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedOrderCreateFulfillmentMutation
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
  </TypedOrderCreateFulfillmentMutation>
);

export default OrderCreateFulfillmentProvider;
