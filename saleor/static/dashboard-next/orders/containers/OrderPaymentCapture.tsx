import * as React from "react";

import {
  OrderCaptureMutation,
  OrderCaptureMutationVariables
} from "../../gql-types";
import { TypedOrderCaptureMutation } from "../mutations";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";

interface OrderPaymentCaptureProviderProps
  extends PartialMutationProviderProps<OrderCaptureMutation> {
  id: string;
  children: PartialMutationProviderRenderProps<
    OrderCaptureMutation,
    OrderCaptureMutationVariables
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
