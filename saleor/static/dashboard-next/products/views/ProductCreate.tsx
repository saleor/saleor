import * as React from "react";

import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import Shop from "../../components/Shop";
import { WindowTitle } from "../../components/WindowTitle";
import i18n from "../../i18n";
import { decimal, getMutationState, maybe } from "../../misc";
import ProductCreatePage, { FormData } from "../components/ProductCreatePage";
import { CategorySearchProvider } from "../containers/CategorySearch";
import { CollectionSearchProvider } from "../containers/CollectionSearch";
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
                  <CategorySearchProvider>
                    {({
                      search: searchCategory,
                      searchOpts: searchCategoryOpts
                    }) => (
                      <CollectionSearchProvider>
                        {({
                          search: searchCollection,
                          searchOpts: searchCollectionOpts
                        }) => (
                          <TypedProductCreateQuery displayLoader>
                            {({ data, loading }) => {
                              const handleSuccess = (data: ProductCreate) => {
                                if (data.productCreate.errors.length === 0) {
                                  pushMessage({
                                    text: i18n.t("Product created")
                                  });
                                  navigate(
                                    productUrl(data.productCreate.product.id)
                                  );
                                }
                              };

                              return (
                                <TypedProductCreateMutation
                                  onCompleted={handleSuccess}
                                >
                                  {(
                                    productCreate,
                                    {
                                      called: productCreateCalled,
                                      data: productCreateData,
                                      loading: productCreateDataLoading
                                    }
                                  ) => {
                                    const handleSubmit = (
                                      formData: FormData
                                    ) => {
                                      productCreate({
                                        variables: {
                                          attributes: formData.attributes,
                                          category: formData.category.value,
                                          chargeTaxes: formData.chargeTaxes,
                                          collections: formData.collections.map(
                                            collection => collection.value
                                          ),
                                          descriptionJson: JSON.stringify(
                                            formData.description
                                          ),
                                          isPublished: formData.available,
                                          name: formData.name,
                                          price: decimal(formData.price),
                                          productType:
                                            formData.productType.value.id,
                                          publicationDate:
                                            formData.publicationDate !== ""
                                              ? formData.publicationDate
                                              : null,
                                          sku: formData.sku,
                                          stockQuantity: formData.stockQuantity !== null ? formData.stockQuantity : 0,
                                        }
                                      });
                                    };

                                    const disabled =
                                      loading || productCreateDataLoading;

                                    const formTransitionState = getMutationState(
                                      productCreateCalled,
                                      productCreateDataLoading,
                                      maybe(
                                        () =>
                                          productCreateData.productCreate.errors
                                      )
                                    );
                                    return (
                                      <>
                                        <WindowTitle
                                          title={i18n.t("Create product")}
                                        />
                                        <ProductCreatePage
                                          currency={maybe(
                                            () => shop.defaultCurrency
                                          )}
                                          categories={maybe(
                                            () =>
                                              searchCategoryOpts.data.categories
                                                .edges,
                                            []
                                          ).map(edge => edge.node)}
                                          collections={maybe(
                                            () =>
                                              searchCollectionOpts.data
                                                .collections.edges,
                                            []
                                          ).map(edge => edge.node)}
                                          disabled={disabled}
                                          errors={maybe(
                                            () =>
                                              productCreateData.productCreate
                                                .errors,
                                            []
                                          )}
                                          fetchCategories={searchCategory}
                                          fetchCollections={searchCollection}
                                          header={i18n.t("New Product")}
                                          productTypes={maybe(() =>
                                            data.productTypes.edges.map(
                                              edge => edge.node
                                            )
                                          )}
                                          onAttributesEdit={
                                            handleAttributesEdit
                                          }
                                          onBack={handleBack}
                                          onSubmit={handleSubmit}
                                          saveButtonBarState={
                                            formTransitionState
                                          }
                                        />
                                      </>
                                    );
                                  }}
                                </TypedProductCreateMutation>
                              );
                            }}
                          </TypedProductCreateQuery>
                        )}
                      </CollectionSearchProvider>
                    )}
                  </CategorySearchProvider>
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
