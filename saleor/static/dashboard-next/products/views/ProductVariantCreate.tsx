import * as React from "react";

import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import Shop from "../../components/Shop";
import { WindowTitle } from "../../components/WindowTitle";
import i18n from "../../i18n";
import { decimal, getMutationState, maybe } from "../../misc";
import ProductVariantCreatePage from "../components/ProductVariantCreatePage";
import { TypedVariantCreateMutation } from "../mutations";
import { TypedProductVariantCreateQuery } from "../queries";
import { VariantCreate } from "../types/VariantCreate";
import { productUrl, productVariantEditUrl } from "../urls";

interface ProductUpdateProps {
  productId: string;
}

interface FormData {
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
  productId
}) => (
  <Shop>
    {shop => (
      <Navigator>
        {navigate => (
          <Messages>
            {pushMessage => (
              <TypedProductVariantCreateQuery
                displayLoader
                variables={{ id: productId }}
                require={["product"]}
              >
                {({ data, loading: productLoading }) => {
                  const handleCreateSuccess = (data: VariantCreate) => {
                    if (data.productVariantCreate.errors.length === 0) {
                      pushMessage({ text: i18n.t("Product created") });
                      navigate(
                        productVariantEditUrl(
                          productId,
                          data.productVariantCreate.productVariant.id
                        )
                      );
                    }
                  };

                  return (
                    <TypedVariantCreateMutation
                      onCompleted={handleCreateSuccess}
                    >
                      {(variantCreate, variantCreateResult) => {
                        const handleBack = () =>
                          navigate(productUrl(productId));
                        const handleSubmit = (formData: FormData) =>
                          variantCreate({
                            variables: {
                              attributes: formData.attributes,
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

                        const disableForm =
                          productLoading || variantCreateResult.loading;

                        const formTransitionstate = getMutationState(
                          variantCreateResult.called,
                          variantCreateResult.loading,
                          maybe(
                            () =>
                              variantCreateResult.data.productVariantCreate
                                .errors
                          )
                        );
                        return (
                          <>
                            <WindowTitle title={i18n.t("Create variant")} />
                            <ProductVariantCreatePage
                              currencySymbol={maybe(() => shop.defaultCurrency)}
                              errors={maybe(
                                () =>
                                  variantCreateResult.data.productVariantCreate
                                    .errors,
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
            )}
          </Messages>
        )}
      </Navigator>
    )}
  </Shop>
);
export default ProductVariant;
