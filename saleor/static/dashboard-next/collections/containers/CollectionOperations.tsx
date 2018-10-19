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
import {
  RemoveCollection,
  RemoveCollectionVariables
} from "../types/RemoveCollection";
import CollectionAssignProductProvider from "./CollectionAssignProductProvider";
import CollectionRemoveProvider from "./CollectionRemove";
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
    removeCollection: PartialMutationProviderOutput<
      RemoveCollection,
      RemoveCollectionVariables
    >;
  }>;
  onHomepageCollectionAssign: (data: AssignHomepageCollection) => void;
  onUpdate: (data: CollectionUpdate) => void;
  onProductAssign: (data: CollectionAssignProduct) => void;
  onRemove: (data: RemoveCollection) => void;
}

const CollectionOperations: React.StatelessComponent<
  CollectionUpdateOperationsProps
> = ({
  children,
  onHomepageCollectionAssign,
  onUpdate,
  onProductAssign,
  onRemove
}) => (
  <CollectionUpdateProvider onSuccess={onUpdate}>
    {updateCollection => (
      <CollectionRemoveProvider onSuccess={onRemove}>
        {removeCollection => (
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
                    removeCollection: {
                      data: removeCollection.data,
                      loading: removeCollection.loading,
                      mutate: variables =>
                        removeCollection.mutate({ variables })
                    },
                    updateCollection: {
                      data: updateCollection.data,
                      loading: updateCollection.loading,
                      mutate: variables =>
                        updateCollection.mutate({ variables })
                    }
                  })
                }
              </HomepageCollectionAssignProvider>
            )}
          </CollectionAssignProductProvider>
        )}
      </CollectionRemoveProvider>
    )}
  </CollectionUpdateProvider>
);
export default CollectionOperations;
