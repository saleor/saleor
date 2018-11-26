import * as React from "react";

import {
  MutationProviderProps,
  MutationProviderRenderProps,
  PartialMutationProviderOutput
} from "../../types";
import { TypedUnassignCollectionProductMutation } from "../mutations";
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
import {
  UnassignCollectionProduct,
  UnassignCollectionProductVariables
} from "../types/UnassignCollectionProduct";
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
    unassignProduct: PartialMutationProviderOutput<
      UnassignCollectionProduct,
      UnassignCollectionProductVariables
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
  onProductUnassign: (data: UnassignCollectionProduct) => void;
  onRemove: (data: RemoveCollection) => void;
}

const CollectionOperations: React.StatelessComponent<
  CollectionUpdateOperationsProps
> = ({
  children,
  onHomepageCollectionAssign,
  onUpdate,
  onProductAssign,
  onProductUnassign,
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
                {assignHomepageCollection => (
                  <TypedUnassignCollectionProductMutation
                    onCompleted={onProductUnassign}
                  >
                    {(unassignProduct, unassignProductOpts) =>
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
                          mutate: variables =>
                            assignProduct.mutate({ variables })
                        },
                        removeCollection: {
                          data: removeCollection.data,
                          loading: removeCollection.loading,
                          mutate: variables =>
                            removeCollection.mutate({ variables })
                        },
                        unassignProduct: {
                          data: unassignProductOpts.data,
                          loading: unassignProductOpts.loading,
                          mutate: variables => unassignProduct({ variables })
                        },
                        updateCollection: {
                          data: updateCollection.data,
                          loading: updateCollection.loading,
                          mutate: variables =>
                            updateCollection.mutate({ variables })
                        }
                      })
                    }
                  </TypedUnassignCollectionProductMutation>
                )}
              </HomepageCollectionAssignProvider>
            )}
          </CollectionAssignProductProvider>
        )}
      </CollectionRemoveProvider>
    )}
  </CollectionUpdateProvider>
);
export default CollectionOperations;
