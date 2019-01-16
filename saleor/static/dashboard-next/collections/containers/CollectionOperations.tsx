import * as React from "react";

import { getMutationProviderData } from "../../misc";
import { PartialMutationProviderOutput } from "../../types";
import {
  TypedCollectionAssignProductMutation,
  TypedCollectionRemoveMutation,
  TypedCollectionUpdateMutation,
  TypedCollectionUpdateWithHomepageMutation,
  TypedUnassignCollectionProductMutation
} from "../mutations";
import {
  CollectionAssignProduct,
  CollectionAssignProductVariables
} from "../types/CollectionAssignProduct";
import {
  CollectionUpdate,
  CollectionUpdateVariables
} from "../types/CollectionUpdate";
import {
  CollectionUpdateWithHomepage,
  CollectionUpdateWithHomepageVariables
} from "../types/CollectionUpdateWithHomepage";
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
      updateCollectionWithHomepage: PartialMutationProviderOutput<
        CollectionUpdateWithHomepage,
        CollectionUpdateWithHomepageVariables
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
  onUpdate: (data: CollectionUpdate) => void;
  onProductAssign: (data: CollectionAssignProduct) => void;
  onProductUnassign: (data: UnassignCollectionProduct) => void;
  onRemove: (data: RemoveCollection) => void;
}

const CollectionOperations: React.StatelessComponent<
  CollectionUpdateOperationsProps
> = ({ children, onUpdate, onProductAssign, onProductUnassign, onRemove }) => (
  <TypedCollectionUpdateMutation onCompleted={onUpdate}>
    {(...updateCollection) => (
      <TypedCollectionRemoveMutation onCompleted={onRemove}>
        {(...removeCollection) => (
          <TypedCollectionAssignProductMutation onCompleted={onProductAssign}>
            {(...assignProduct) => (
              <TypedCollectionUpdateWithHomepageMutation onCompleted={onUpdate}>
                {(...updateWithHomepage) => (
                  <TypedUnassignCollectionProductMutation
                    onCompleted={onProductUnassign}
                  >
                    {(...unassignProduct) =>
                      children({
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
                        ),
                        updateCollectionWithHomepage: getMutationProviderData(
                          ...updateWithHomepage
                        )
                      })
                    }
                  </TypedUnassignCollectionProductMutation>
                )}
              </TypedCollectionUpdateWithHomepageMutation>
            )}
          </TypedCollectionAssignProductMutation>
        )}
      </TypedCollectionRemoveMutation>
    )}
  </TypedCollectionUpdateMutation>
);
export default CollectionOperations;
