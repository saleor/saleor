import * as React from "react";

import { TypedCollectionAssignProductMutation } from "../mutations";
import {
  CollectionAssignProduct,
  CollectionAssignProductVariables
} from "../types/CollectionAssignProduct";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";

interface CollectionAssignProductProviderProps
  extends PartialMutationProviderProps<CollectionAssignProduct> {
  children: PartialMutationProviderRenderProps<
    CollectionAssignProduct,
    CollectionAssignProductVariables
  >;
}

const CollectionUUpdateProvider: React.StatelessComponent<
  CollectionAssignProductProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedCollectionAssignProductMutation
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
  </TypedCollectionAssignProductMutation>
);

export default CollectionUUpdateProvider;
