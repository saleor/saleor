import * as React from "react";

import { TypedCollectionRemoveMutation } from "../mutations";
import {
  RemoveCollection,
  RemoveCollectionVariables
} from "../types/RemoveCollection";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";

interface CollectionRemoveProviderProps
  extends PartialMutationProviderProps<RemoveCollection> {
  children: PartialMutationProviderRenderProps<
    RemoveCollection,
    RemoveCollectionVariables
  >;
}

const CollectionRemoveProvider: React.StatelessComponent<
  CollectionRemoveProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedCollectionRemoveMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedCollectionRemoveMutation>
);

export default CollectionRemoveProvider;
