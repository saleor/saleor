import * as React from "react";

import { TypedOrderAddNoteMutation } from "../mutations";
import { OrderAddNote, OrderAddNoteVariables } from "../types/OrderAddNote";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";

interface OrderNoteAddProviderProps
  extends PartialMutationProviderProps<OrderAddNote> {
  children: PartialMutationProviderRenderProps<
    OrderAddNote,
    OrderAddNoteVariables
  >;
}

const OrderNoteAddProvider: React.StatelessComponent<
  OrderNoteAddProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedOrderAddNoteMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedOrderAddNoteMutation>
);

export default OrderNoteAddProvider;
