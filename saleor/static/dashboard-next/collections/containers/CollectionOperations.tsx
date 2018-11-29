import * as React from "react";

import { getMutationProviderData } from "../../misc";
import { PartialMutationProviderOutput } from "../../types";
import {
  TypedAssignHomepageCollectionMutation,
  TypedCollectionAssignProductMutation,
  TypedCollectionRemoveMutation,
  TypedCollectionUpdateMutation,
  TypedUnassignCollectionProductMutation
} from "../mutations";
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

interface CollectionUpdateOperationsProps {
  children: (
    props: {
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
    }
  ) => React.ReactNode;
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
  <TypedCollectionUpdateMutation onCompleted={onUpdate}>
    {(...updateCollection) => (
      <TypedCollectionRemoveMutation onCompleted={onRemove}>
        {(...removeCollection) => (
          <TypedCollectionAssignProductMutation onCompleted={onProductAssign}>
            {(...assignProduct) => (
              <TypedAssignHomepageCollectionMutation
                onCompleted={onHomepageCollectionAssign}
              >
                {(...assignHomepageCollection) => (
                  <TypedUnassignCollectionProductMutation
                    onCompleted={onProductUnassign}
                  >
                    {(...unassignProduct) =>
                      children({
                        assignHomepageCollection: getMutationProviderData(
                          ...assignHomepageCollection
                        ),
                        assignProduct: getMutationProviderData(
                          ...assignProduct
                        ),
                        removeCollection: getMutationProviderData(
                          ...removeCollection
                        ),
                        unassignProduct: getMutationProviderData(
                          ...unassignProduct
                        ),
                        updateCollection: getMutationProviderData(
                          ...updateCollection
                        )
                      })
                    }
                  </TypedUnassignCollectionProductMutation>
                )}
              </TypedAssignHomepageCollectionMutation>
            )}
          </TypedCollectionAssignProductMutation>
        )}
      </TypedCollectionRemoveMutation>
    )}
  </TypedCollectionUpdateMutation>
);
export default CollectionOperations;
