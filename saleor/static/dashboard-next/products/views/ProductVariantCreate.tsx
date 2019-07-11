import React from "react";

import { WindowTitle } from "@saleor/components/WindowTitle";
import useNavigator from "@saleor/hooks/useNavigator";
import useNotifier from "@saleor/hooks/useNotifier";
import useShop from "@saleor/hooks/useShop";
import i18n from "../../i18n";
import { decimal, getMutationState, maybe } from "../../misc";
import ProductVariantCreatePage, {
  ProductVariantCreatePageSubmitData
} from "../components/ProductVariantCreatePage";
import { TypedVariantCreateMutation } from "../mutations";
import { TypedProductVariantCreateQuery } from "../queries";
import { VariantCreate } from "../types/VariantCreate";
import { productUrl, productVariantEditUrl } from "../urls";

interface ProductUpdateProps {
  productId: string;
}

export const ProductVariant: React.StatelessComponent<ProductUpdateProps> = ({
  productId
}) => {
  const navigate = useNavigator();
  const notify = useNotifier();
  const shop = useShop();

  return (
    <TypedProductVariantCreateQuery
      displayLoader
      variables={{ id: productId }}
      require={["product"]}
    >
      {({ data, loading: productLoading }) => {
        const handleCreateSuccess = (data: VariantCreate) => {
          if (data.productVariantCreate.errors.length === 0) {
            notify({ text: i18n.t("Product created") });
            navigate(
              productVariantEditUrl(
                productId,
                data.productVariantCreate.productVariant.id
              )
            );
          }
        };

        return (
          <TypedVariantCreateMutation onCompleted={handleCreateSuccess}>
            {(variantCreate, variantCreateResult) => {
              const handleBack = () => navigate(productUrl(productId));
              const handleSubmit = (
                formData: ProductVariantCreatePageSubmitData
              ) =>
                variantCreate({
                  variables: {
                    attributes: formData.attributes.map(attribute => ({
                      id: attribute.id,
                      values: [attribute.value]
                    })),
                    costPrice: decimal(formData.costPrice),
                    priceOverride: decimal(formData.priceOverride),
                    product: productId,
                    quantity: formData.quantity || null,
                    sku: formData.sku,
                    trackInventory: true
                  }
                });
              const handleVariantClick = (id: string) =>
                navigate(productVariantEditUrl(productId, id));

              const disableForm = productLoading || variantCreateResult.loading;

              const formTransitionstate = getMutationState(
                variantCreateResult.called,
                variantCreateResult.loading,
                maybe(
                  () => variantCreateResult.data.productVariantCreate.errors
                )
              );
              return (
                <>
                  <WindowTitle title={i18n.t("Create variant")} />
                  <ProductVariantCreatePage
                    currencySymbol={maybe(() => shop.defaultCurrency)}
                    errors={maybe(
                      () =>
                        variantCreateResult.data.productVariantCreate.errors,
                      []
                    )}
                    header={i18n.t("Add Variant")}
                    loading={disableForm}
                    product={maybe(() => data.product)}
                    onBack={handleBack}
                    onSubmit={handleSubmit}
                    onVariantClick={handleVariantClick}
                    saveButtonBarState={formTransitionstate}
                  />
                </>
              );
            }}
          </TypedVariantCreateMutation>
        );
      }}
    </TypedProductVariantCreateQuery>
  );
};
export default ProductVariant;
