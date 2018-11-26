import * as React from "react";

import { TypedOrderRefundMutation } from "../mutations";
import { OrderRefund, OrderRefundVariables } from "../types/OrderRefund";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";

interface OrderPaymentCaptureProviderProps
  extends PartialMutationProviderProps<OrderRefund> {
  id: string;
  children: PartialMutationProviderRenderProps<
    OrderRefund,
    OrderRefundVariables
  >;
}

const OrderPaymentCaptureProvider: React.StatelessComponent<
  OrderPaymentCaptureProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedOrderRefundMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedOrderRefundMutation>
);

export default OrderPaymentCaptureProvider;
