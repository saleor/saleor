import * as React from "react";

import { TypedAssignHomepageCollectionMutation } from "../mutations";
import {
  AssignHomepageCollection,
  AssignHomepageCollectionVariables
} from "../types/AssignHomepageCollection";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";

interface HomepageCollectionAssignProviderProps
  extends PartialMutationProviderProps<AssignHomepageCollection> {
  children: PartialMutationProviderRenderProps<
    AssignHomepageCollection,
    AssignHomepageCollectionVariables
  >;
}

const HomepageCollectionAssignProvider: React.StatelessComponent<
  HomepageCollectionAssignProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedAssignHomepageCollectionMutation
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
  </TypedAssignHomepageCollectionMutation>
);

export default HomepageCollectionAssignProvider;
