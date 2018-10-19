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
  CollectionAssignProduct,
  CollectionAssignProductVariables
} from "../types/CollectionAssignProduct";
import {
  CollectionUpdate,
  CollectionUpdateVariables
} from "../types/CollectionUpdate";
import CollectionAssignProductProvider from "./CollectionAssignProductProvider";
import CollectionUpdateProvider from "./CollectionUpdateProvider";
import HomepageCollectionAssignProvider from "./HomepageCollectionAssignProvider";

interface CollectionUpdateOperationsProps extends MutationProviderProps {
  children: MutationProviderRenderProps<{
    assignHomepageCollection: PartialMutationProviderOutput<
      AssignHomepageCollection,
      AssignHomepageCollectionVariables
    >;
    assignProduct: PartialMutationProviderOutput<
      CollectionAssignProduct,
      CollectionAssignProductVariables
    >;
    updateCollection: PartialMutationProviderOutput<
      CollectionUpdate,
      CollectionUpdateVariables
    >;
  }>;
  onHomepageCollectionAssign: (data: AssignHomepageCollection) => void;
  onUpdate: (data: CollectionUpdate) => void;
  onProductAssign: (data: CollectionAssignProduct) => void;
}

const CollectionOperations: React.StatelessComponent<
  CollectionUpdateOperationsProps
> = ({ children, onHomepageCollectionAssign, onUpdate, onProductAssign }) => (
  <CollectionUpdateProvider onSuccess={onUpdate}>
    {updateCollection => (
      <CollectionAssignProductProvider onSuccess={onProductAssign}>
        {assignProduct => (
          <HomepageCollectionAssignProvider
            onSuccess={onHomepageCollectionAssign}
          >
            {assignHomepageCollection =>
              children({
                assignHomepageCollection: {
                  data: assignHomepageCollection.data,
                  loading: assignHomepageCollection.loading,
                  mutate: variables =>
                    assignHomepageCollection.mutate({ variables })
                },
                assignProduct: {
                  data: assignProduct.data,
                  loading: assignProduct.loading,
                  mutate: variables => assignProduct.mutate({ variables })
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
      </CollectionAssignProductProvider>
    )}
  </CollectionUpdateProvider>
);
export default CollectionOperations;
