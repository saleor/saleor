import * as React from "react";

import { productUrl, productVariantEditUrl } from "..";
import * as placeholderImg from "../../../images/placeholder255x255.png";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Navigator from "../../components/Navigator";
import ProductVariantPage from "../components/ProductVariantPage";
import ProductVariantOperations from "../containers/ProductVariantOperations";
import { productVariantQuery, TypedProductVariantQuery } from "../queries";

interface ProductUpdateProps {
  variantId: string;
  productId: string;
}

export const ProductVariant: React.StatelessComponent<ProductUpdateProps> = ({
  variantId,
  productId
}) => (
  <Navigator>
    {navigate => {
      return (
        <TypedProductVariantQuery
          query={productVariantQuery}
          variables={{ id: variantId }}
          fetchPolicy="network-only"
        >
          {({ data, loading, error, fetchMore }) => {
            if (error) {
              return <ErrorMessageCard message="Something went wrong" />;
            }
            const variant = data ? data.productVariant : undefined;
            return (
              <ProductVariantOperations
                productId={productId}
                variantId={variant ? variant.id : ""}
              >
                {({ deleteVariant, updateVariant }) => (
                  <ProductVariantPage
                    loading={loading}
                    placeholderImage={placeholderImg}
                    variant={variant}
                    onBack={() => {
                      navigate(productUrl(productId));
                    }}
                    onDelete={deleteVariant}
                    onImageSelect={() => {}}
                    onSubmit={data => {
                      if (variant) {
                        // fix attributes
                        const attributes = variant.attributes
                          .map(item => ({
                            slug: item.attribute.slug,
                            values: item.attribute.values
                          }))
                          .map(({ slug, values }) => {
                            const valueSlug = data[slug];
                            const value = values.filter(
                              item => item.slug === valueSlug
                            );
                            return {
                              slug,
                              value:
                                value && value[0] ? value[0].name : valueSlug
                            };
                          });

                        updateVariant({
                          attributes,
                          costPrice: data.costPrice ? data.costPrice : null,
                          id: variant.id,
                          priceOverride: data.priceOverride
                            ? data.priceOverride
                            : null,
                          product: productId,
                          quantity: data.stock,
                          sku: data.sku,
                          trackInventory: true // FIXME: missing in UI
                        });
                      }
                    }}
                    onVariantClick={variantId => {
                      navigate(productVariantEditUrl(productId, variantId));
                    }}
                  />
                )}
              </ProductVariantOperations>
            );
          }}
        </TypedProductVariantQuery>
      );
    }}
  </Navigator>
);
export default ProductVariant;
