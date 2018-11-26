import * as React from "react";

import { TypedOrderMarkAsPaidMutation } from "../mutations";
import {
  OrderMarkAsPaid,
  OrderMarkAsPaidVariables
} from "../types/OrderMarkAsPaid";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";

interface OrderPaymentCaptureProviderProps
  extends PartialMutationProviderProps<OrderMarkAsPaid> {
  children: PartialMutationProviderRenderProps<
    OrderMarkAsPaid,
    OrderMarkAsPaidVariables
  >;
}

const OrderMarkAsPaidProvider: React.StatelessComponent<
  OrderPaymentCaptureProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedOrderMarkAsPaidMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedOrderMarkAsPaidMutation>
);

export default OrderMarkAsPaidProvider;
