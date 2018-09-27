import * as React from "react";

import { productUrl, productVariantEditUrl } from "..";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import i18n from "../../i18n";
import { decimal, maybe } from "../../misc";
import ProductVariantCreatePage from "../components/ProductVariantCreatePage";
import { TypedVariantCreateMutation } from "../mutations";
import {
  productVariantCreateQuery,
  TypedProductVariantCreateQuery
} from "../queries";
import { VariantCreate } from "../types/VariantCreate";

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
  <Navigator>
    {navigate => (
      <Messages>
        {pushMessage => (
          <TypedProductVariantCreateQuery
            query={productVariantCreateQuery}
            variables={{ id: productId }}
          >
            {({ data, error, loading: productLoading }) => {
              if (error) {
                return (
                  <ErrorMessageCard message={i18n.t("Something went wrong")} />
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
                      productId,
                      data.productVariantCreate.productVariant.id
                    )
                  );
                }
              };

              return (
                <TypedVariantCreateMutation onCompleted={handleCreateSuccess}>
                  {(variantCreate, variantCreateResult) => {
                    if (variantCreateResult.error) {
                      return (
                        <ErrorMessageCard
                          message={i18n.t("Something went wrong")}
                        />
                      );
                    }

                    const handleBack = () => navigate(productUrl(productId));
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

                    const loading =
                      productLoading || variantCreateResult.loading;
                    return (
                      <ProductVariantCreatePage
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
);
export default ProductVariant;
