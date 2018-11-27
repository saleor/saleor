import * as React from "react";

import { TypedCollectionUpdateMutation } from "../mutations";
import {
  CollectionUpdate,
  CollectionUpdateVariables
} from "../types/CollectionUpdate";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";

interface CollectionUpdateProviderProps
  extends PartialMutationProviderProps<CollectionUpdate> {
  children: PartialMutationProviderRenderProps<
    CollectionUpdate,
    CollectionUpdateVariables
  >;
}

const CollectionUUpdateProvider: React.StatelessComponent<
  CollectionUpdateProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedCollectionUpdateMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { called, data, error, loading }) =>
      children({
        called,
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedCollectionUpdateMutation>
);

export default CollectionUUpdateProvider;
