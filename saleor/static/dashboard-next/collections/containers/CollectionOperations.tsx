import * as React from "react";

import {
  MutationProviderProps,
  MutationProviderRenderProps,
  PartialMutationProviderOutput
} from "../..";
import {
  AssignHomepageCollection,
  AssignHomepageCollectionVariables
} from "../types/AssignHomepageCollection";
import {
  CollectionUpdate,
  CollectionUpdateVariables
} from "../types/CollectionUpdate";
import CollectionUpdateProvider from "./CollectionUpdateProvider";
import HomepageCollectionAssignProvider from "./HomepageCollectionAssignProvider";

interface CollectionUpdateOperationsProps extends MutationProviderProps {
  children: MutationProviderRenderProps<{
    assignHomepageCollection: PartialMutationProviderOutput<
      AssignHomepageCollection,
      AssignHomepageCollectionVariables
    >;
    updateCollection: PartialMutationProviderOutput<
      CollectionUpdate,
      CollectionUpdateVariables
    >;
  }>;
  onHomepageCollectionAssign: (data: AssignHomepageCollection) => void;
  onUpdate: (data: CollectionUpdate) => void;
}

const CollectionOperations: React.StatelessComponent<
  CollectionUpdateOperationsProps
> = ({ children, onHomepageCollectionAssign, onUpdate }) => (
  <CollectionUpdateProvider onSuccess={onUpdate}>
    {updateCollection => (
      <HomepageCollectionAssignProvider onSuccess={onHomepageCollectionAssign}>
        {assignHomepageCollection =>
          children({
            assignHomepageCollection: {
              data: assignHomepageCollection.data,
              loading: assignHomepageCollection.loading,
              mutate: variables =>
                assignHomepageCollection.mutate({ variables })
            },
            updateCollection: {
              data: updateCollection.data,
              loading: updateCollection.loading,
              mutate: variables => updateCollection.mutate({ variables })
            }
          })
        }
      </HomepageCollectionAssignProvider>
    )}
  </CollectionUpdateProvider>
);
export default CollectionOperations;
