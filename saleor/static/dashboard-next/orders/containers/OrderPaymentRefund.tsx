import * as React from "react";

import {
  OrderRefundMutation,
  OrderRefundMutationVariables
} from "../../gql-types";
import { TypedOrderRefundMutation } from "../mutations";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";

interface OrderPaymentCaptureProviderProps
  extends PartialMutationProviderProps<OrderRefundMutation> {
  id: string;
  children: PartialMutationProviderRenderProps<
    OrderRefundMutation,
    OrderRefundMutationVariables
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
