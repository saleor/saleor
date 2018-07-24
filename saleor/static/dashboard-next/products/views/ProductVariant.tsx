import * as React from "react";

import { ApolloError } from "apollo-client";
import { productUrl, productVariantEditUrl } from "..";
import * as placeholderImg from "../../../images/placeholder255x255.png";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import i18n from "../../i18n";
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
    {navigate => (
      <Messages>
        {pushMessage => (
          <TypedProductVariantQuery
            query={productVariantQuery}
            variables={{ id: variantId }}
            fetchPolicy="network-only"
          >
            {({ data, loading, error }) => {
              if (error) {
                return <ErrorMessageCard message="Something went wrong" />;
              }
              const variant = data ? data.productVariant : undefined;
              const handleBack = () => navigate(productUrl(productId));
              const handleDelete = () => {
                pushMessage({ text: i18n.t("Variant removed") });
                navigate(productUrl(productId));
              };
              const handleError = (error: ApolloError) => {
                console.error(error.message);
                pushMessage({ text: i18n.t("Something went wrong") });
              };
              const handleUpdate = () =>
                pushMessage({ text: i18n.t("Changes saved") });
              return (
                <ProductVariantOperations
                  productId={productId}
                  id={variantId}
                  onDelete={handleDelete}
                  onError={handleError}
                  onUpdate={handleUpdate}
                >
                  {({ deleteVariant, updateVariant }) => {
                    const disableFormSave =
                      loading || deleteVariant.loading || updateVariant.loading;
                    const formSubmitState = disableFormSave
                      ? "loading"
                      : "idle";
                    return (
                      <ProductVariantPage
                        errors={
                          updateVariant &&
                          updateVariant.data &&
                          updateVariant.data.productVariantUpdate &&
                          updateVariant.data.productVariantUpdate.errors
                            ? updateVariant.data.productVariantUpdate.errors
                            : []
                        }
                        saveButtonBarState={formSubmitState}
                        loading={disableFormSave}
                        placeholderImage={placeholderImg}
                        variant={variant}
                        header={
                          variant ? variant.name || variant.sku : undefined
                        }
                        onBack={handleBack}
                        onDelete={() => deleteVariant.mutate(variantId)}
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
                                const valueSlug = data[slug].value;
                                const value = values.filter(
                                  item => item.slug === valueSlug
                                );
                                return {
                                  slug,
                                  value:
                                    value && value[0]
                                      ? value[0].name
                                      : valueSlug
                                };
                              });

                            updateVariant.mutate({
                              attributes,
                              costPrice: data.costPrice ? data.costPrice : null,
                              id: variantId,
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
                    );
                  }}
                </ProductVariantOperations>
              );
            }}
          </TypedProductVariantQuery>
        )}
      </Messages>
    )}
  </Navigator>
);
export default ProductVariant;
