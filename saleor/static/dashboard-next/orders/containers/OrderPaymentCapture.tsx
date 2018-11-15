import * as React from "react";

import { TypedOrderCaptureMutation } from "../mutations";
import { OrderCapture, OrderCaptureVariables } from "../types/OrderCapture";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";

interface OrderPaymentCaptureProviderProps
  extends PartialMutationProviderProps<OrderCapture> {
  id: string;
  children: PartialMutationProviderRenderProps<
    OrderCapture,
    OrderCaptureVariables
  >;
}

const OrderPaymentCaptureProvider: React.StatelessComponent<
  OrderPaymentCaptureProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedOrderCaptureMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedOrderCaptureMutation>
);

export default OrderPaymentCaptureProvider;
