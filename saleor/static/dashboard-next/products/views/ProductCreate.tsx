import * as React from "react";

import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import Shop from "../../components/Shop";
import { WindowTitle } from "../../components/WindowTitle";
import i18n from "../../i18n";
import { decimal, getMutationState, maybe } from "../../misc";
import ProductCreatePage from "../components/ProductCreatePage";
import { TypedProductCreateMutation } from "../mutations";
import { TypedProductCreateQuery } from "../queries";
import { ProductCreate } from "../types/ProductCreate";
import { productListUrl, productUrl } from "../urls";

interface ProductUpdateProps {
  id: string;
}

export const ProductUpdate: React.StatelessComponent<
  ProductUpdateProps
> = () => (
  <Shop>
    {shop => (
      <Messages>
        {pushMessage => {
          return (
            <Navigator>
              {navigate => {
                const handleAttributesEdit = undefined;
                const handleBack = () => navigate(productListUrl());

                return (
                  <TypedProductCreateQuery displayLoader>
                    {({ data, loading }) => {
                      const handleSuccess = (data: ProductCreate) => {
                        if (data.productCreate.errors.length === 0) {
                          pushMessage({ text: i18n.t("Product created") });
                          navigate(productUrl(data.productCreate.product.id));
                        }
                      };

                      return (
                        <TypedProductCreateMutation onCompleted={handleSuccess}>
                          {(
                            productCreate,
                            {
                              called: productCreateCalled,
                              data: productCreateData,
                              loading: productCreateDataLoading
                            }
                          ) => {
                            const handleSubmit = formData => {
                              productCreate({
                                variables: {
                                  attributes: formData.attributes,
                                  availableOn:
                                    formData.availableOn !== ""
                                      ? formData.availableOn
                                      : null,
                                  category: formData.category,
                                  chargeTaxes: formData.chargeTaxes,
                                  collections: formData.collections,
                                  description: formData.description,
                                  isPublished: formData.available,
                                  name: formData.name,
                                  price: decimal(formData.price),
                                  productType: formData.productType.value.id
                                }
                              });
                            };

                            const disabled =
                              loading || productCreateDataLoading;

                            const formTransitionState = getMutationState(
                              productCreateCalled,
                              productCreateDataLoading,
                              maybe(
                                () => productCreateData.productCreate.errors
                              )
                            );
                            return (
                              <>
                                <WindowTitle title={i18n.t("Create product")} />
                                <ProductCreatePage
                                  currency={maybe(() => shop.defaultCurrency)}
                                  categories={
                                    data && data.categories
                                      ? data.categories.edges.map(
                                          edge => edge.node
                                        )
                                      : undefined
                                  }
                                  collections={
                                    data && data.collections
                                      ? data.collections.edges.map(
                                          edge => edge.node
                                        )
                                      : undefined
                                  }
                                  disabled={disabled}
                                  errors={
                                    productCreateData &&
                                    productCreateData.productCreate &&
                                    productCreateData.productCreate.errors
                                      ? productCreateData.productCreate.errors
                                      : []
                                  }
                                  header={i18n.t("New Product")}
                                  productTypes={
                                    data && data.productTypes
                                      ? data.productTypes.edges.map(
                                          edge => edge.node
                                        )
                                      : undefined
                                  }
                                  onAttributesEdit={handleAttributesEdit}
                                  onBack={handleBack}
                                  onSubmit={handleSubmit}
                                  saveButtonBarState={formTransitionState}
                                />
                              </>
                            );
                          }}
                        </TypedProductCreateMutation>
                      );
                    }}
                  </TypedProductCreateQuery>
                );
              }}
            </Navigator>
          );
        }}
      </Messages>
    )}
  </Shop>
);
export default ProductUpdate;
