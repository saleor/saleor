import * as React from "react";

import { TypedOrderShippingMethodUpdateMutation } from "../mutations";
import {
  OrderShippingMethodUpdate,
  OrderShippingMethodUpdateVariables
} from "../types/OrderShippingMethodUpdate";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";

interface OrderShippingMethodUpdateProviderProps
  extends PartialMutationProviderProps<OrderShippingMethodUpdate> {
  children: PartialMutationProviderRenderProps<
    OrderShippingMethodUpdate,
    OrderShippingMethodUpdateVariables
  >;
}

const OrderShippingMethodUpdateProvider: React.StatelessComponent<
  OrderShippingMethodUpdateProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedOrderShippingMethodUpdateMutation
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
  </TypedOrderShippingMethodUpdateMutation>
);

export default OrderShippingMethodUpdateProvider;
