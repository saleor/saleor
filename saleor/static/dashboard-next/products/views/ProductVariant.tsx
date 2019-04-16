import * as React from "react";

import * as placeholderImg from "../../../images/placeholder255x255.png";
import { WindowTitle } from "../../components/WindowTitle";
import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import i18n from "../../i18n";
import { decimal, getMutationState, maybe } from "../../misc";
import ProductVariantDeleteDialog from "../components/ProductVariantDeleteDialog";
import ProductVariantPage from "../components/ProductVariantPage";
import ProductVariantOperations from "../containers/ProductVariantOperations";
import { TypedProductVariantQuery } from "../queries";
import { VariantUpdate } from "../types/VariantUpdate";
import {
  productUrl,
  productVariantAddUrl,
  productVariantEditUrl,
  ProductVariantEditUrlQueryParams
} from "../urls";

interface ProductUpdateProps {
  variantId: string;
  productId: string;
  params: ProductVariantEditUrlQueryParams;
}

interface FormData {
  id: string;
  attributes?: Array<{
    slug: string;
    value: string;
  }>;
  costPrice?: string;
  priceOverride?: string;
  quantity: number;
  sku: string;
}

export const ProductVariant: React.StatelessComponent<ProductUpdateProps> = ({
  variantId,
  productId,
  params
}) => {
  const navigate = useNavigator();
  const notify = useNotifier();

  return (
    <TypedProductVariantQuery
      displayLoader
      variables={{ id: variantId }}
      require={["productVariant"]}
    >
      {({ data, loading }) => {
        const variant = data ? data.productVariant : undefined;
        const handleBack = () => navigate(productUrl(productId));
        const handleDelete = () => {
          notify({ text: i18n.t("Variant removed") });
          navigate(productUrl(productId));
        };
        const handleUpdate = (data: VariantUpdate) => {
          if (!maybe(() => data.productVariantUpdate.errors.length)) {
            notify({ text: i18n.t("Changes saved") });
          }
        };

        return (
          <ProductVariantOperations
            onDelete={handleDelete}
            onUpdate={handleUpdate}
          >
            {({ assignImage, deleteVariant, updateVariant, unassignImage }) => {
              const disableFormSave =
                loading ||
                deleteVariant.opts.loading ||
                updateVariant.opts.loading ||
                assignImage.opts.loading ||
                unassignImage.opts.loading;
              const formTransitionState = getMutationState(
                updateVariant.opts.called,
                updateVariant.opts.loading,
                maybe(() => updateVariant.opts.data.productVariantUpdate.errors)
              );
              const removeTransitionState = getMutationState(
                deleteVariant.opts.called,
                deleteVariant.opts.loading,
                maybe(() => deleteVariant.opts.data.productVariantDelete.errors)
              );
              const handleImageSelect = (id: string) => () => {
                if (variant) {
                  if (
                    variant.images &&
                    variant.images.map(image => image.id).indexOf(id) !== -1
                  ) {
                    unassignImage.mutate({
                      imageId: id,
                      variantId: variant.id
                    });
                  } else {
                    assignImage.mutate({
                      imageId: id,
                      variantId: variant.id
                    });
                  }
                }
              };

              return (
                <>
                  <WindowTitle title={maybe(() => data.productVariant.name)} />
                  <ProductVariantPage
                    errors={maybe(
                      () => updateVariant.opts.data.productVariantUpdate.errors,
                      []
                    )}
                    saveButtonBarState={formTransitionState}
                    loading={disableFormSave}
                    placeholderImage={placeholderImg}
                    variant={variant}
                    header={variant ? variant.name || variant.sku : undefined}
                    onAdd={() => navigate(productVariantAddUrl(productId))}
                    onBack={handleBack}
                    onDelete={() =>
                      navigate(
                        productVariantEditUrl(productId, variantId, {
                          action: "remove"
                        })
                      )
                    }
                    onImageSelect={handleImageSelect}
                    onSubmit={(data: FormData) => {
                      if (variant) {
                        updateVariant.mutate({
                          attributes: data.attributes ? data.attributes : null,
                          costPrice: decimal(data.costPrice),
                          id: variantId,
                          priceOverride: decimal(data.priceOverride),
                          quantity: data.quantity || null,
                          sku: data.sku,
                          trackInventory: true // FIXME: missing in UI
                        });
                      }
                    }}
                    onVariantClick={variantId => {
                      navigate(productVariantEditUrl(productId, variantId));
                    }}
                  />
                  <ProductVariantDeleteDialog
                    confirmButtonState={removeTransitionState}
                    onClose={() =>
                      navigate(productVariantEditUrl(productId, variantId))
                    }
                    onConfirm={() =>
                      deleteVariant.mutate({
                        id: variantId
                      })
                    }
                    open={params.action === "remove"}
                    name={maybe(() => data.productVariant.name)}
                  />
                </>
              );
            }}
          </ProductVariantOperations>
        );
      }}
    </TypedProductVariantQuery>
  );
};
export default ProductVariant;
