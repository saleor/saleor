import * as React from "react";

import ErrorMessageCard from "../../components/ErrorMessageCard";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import Shop from "../../components/Shop";
import { WindowTitle } from "../../components/WindowTitle";
import i18n from "../../i18n";
import { decimal, maybe } from "../../misc";
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
              <TypedProductVariantCreateQuery variables={{ id: productId }}>
                {({ data, error, loading: productLoading }) => {
                  if (error) {
                    return (
                      <ErrorMessageCard
                        message={i18n.t("Something went wrong")}
                      />
                    );
                  }

                  const handleCreateSuccess = (data: VariantCreate) => {
                    if (
                      data.productVariantCreate.errors &&
                      data.productVariantCreate.errors.length === 0
                    ) {
                      pushMessage({ text: i18n.t("Product created") });
                      navigate(
                        productVariantEditUrl(
                          encodeURIComponent(productId),
                          encodeURIComponent(
                            data.productVariantCreate.productVariant.id
                          )
                        )
                      );
                    }
                  };

                  return (
                    <TypedVariantCreateMutation
                      onCompleted={handleCreateSuccess}
                    >
                      {(variantCreate, variantCreateResult) => {
                        if (variantCreateResult.error) {
                          return (
                            <ErrorMessageCard
                              message={i18n.t("Something went wrong")}
                            />
                          );
                        }

                        const handleBack = () =>
                          navigate(productUrl(encodeURIComponent(productId)));
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
                          navigate(
                            productVariantEditUrl(
                              encodeURIComponent(productId),
                              encodeURIComponent(id)
                            )
                          );

                        const loading =
                          productLoading || variantCreateResult.loading;
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
                              loading={loading}
                              product={maybe(() => data.product)}
                              onBack={handleBack}
                              onSubmit={handleSubmit}
                              onVariantClick={handleVariantClick}
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
