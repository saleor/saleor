import * as React from "react";

import {
  OrderCreateFulfillmentMutation,
  OrderCreateFulfillmentMutationVariables
} from "../../gql-types";
import { TypedOrderCreateFulfillmentMutation } from "../mutations";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";

interface OrderCreateFulfillmentProviderProps
  extends PartialMutationProviderProps<OrderCreateFulfillmentMutation> {
  id: string;
  children: PartialMutationProviderRenderProps<
    OrderCreateFulfillmentMutation,
    OrderCreateFulfillmentMutationVariables
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
