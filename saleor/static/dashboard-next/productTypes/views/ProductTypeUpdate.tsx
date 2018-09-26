import * as React from "react";
import Navigator from "../../components/Navigator";

import { productTypeListUrl } from "..";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Messages from "../../components/messages";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import ProductTypeDetailsPage, {
  ProductTypeForm
} from "../components/ProductTypeDetailsPage";
import { AttributeSearchProvider } from "../containers/AttributeSearch";
import ProductTypeOperations from "../containers/ProductTypeOperations";
import { TypedProductTypeDetailsQuery } from "../queries";
import { ProductTypeDelete } from "../types/ProductTypeDelete";
import { ProductTypeUpdate as ProductTypeUpdateMutation } from "../types/ProductTypeUpdate";

interface ProductTypeUpdateProps {
  id: string;
}

export const ProductTypeUpdate: React.StatelessComponent<
  ProductTypeUpdateProps
> = ({ id }) => (
  <Messages>
    {pushMessage => (
      <Navigator>
        {navigate => (
          <TypedProductTypeDetailsQuery variables={{ id }}>
            {({ data, error, loading: dataLoading }) => {
              if (error) {
                return (
                  <ErrorMessageCard
                    message={i18n.t("Something went terribly wrong")}
                  />
                );
              }
              return (
                <AttributeSearchProvider>
                  {(searchAttribute, searchState) => {
                    const handleDeleteSuccess = (
                      deleteData: ProductTypeDelete
                    ) => {
                      if (deleteData.productTypeDelete.errors.length === 0) {
                        pushMessage({
                          text: i18n.t("Successfully deleted product type")
                        });
                        navigate(productTypeListUrl);
                      }
                    };
                    const handleUpdateSuccess = (
                      updateData: ProductTypeUpdateMutation
                    ) => {
                      if (updateData.productTypeUpdate.errors.length === 0) {
                        pushMessage({
                          text: i18n.t("Successfully updated product type")
                        });
                      }
                    };
                    return (
                      <ProductTypeOperations
                        id={id}
                        onDelete={handleDeleteSuccess}
                        onUpdate={handleUpdateSuccess}
                      >
                        {({
                          deleteProductType,
                          errors,
                          loading: mutationLoading,
                          updateProductType
                        }) => {
                          const handleDelete = () =>
                            deleteProductType.mutate({ id });
                          const handleUpdate = (formData: ProductTypeForm) => {
                            updateProductType.mutate({
                              id,
                              input: {
                                hasVariants: formData.hasVariants,
                                isShippingRequired: formData.isShippingRequired,
                                name: formData.name,
                                productAttributes: formData.productAttributes.map(
                                  choice => choice.value
                                ),
                                taxRate: formData.taxRate,
                                variantAttributes: formData.variantAttributes.map(
                                  choice => choice.value
                                ),
                                weight: formData.weight
                              }
                            });
                          };
                          const loading = mutationLoading || dataLoading;
                          return (
                            <ProductTypeDetailsPage
                              defaultWeightUnit={maybe(
                                () => data.shop.defaultWeightUnit
                              )}
                              disabled={loading}
                              errors={errors}
                              pageTitle={
                                data && data.productType
                                  ? data.productType.name
                                  : undefined
                              }
                              productType={maybe(() => data.productType)}
                              saveButtonBarState={
                                loading ? "loading" : "default"
                              }
                              searchLoading={maybe(() => searchState.loading)}
                              searchResults={maybe(
                                () =>
                                  searchState.data.attributes.edges.map(
                                    edge => edge.node
                                  ),
                                []
                              )}
                              onAttributeSearch={searchAttribute}
                              onBack={() => navigate(productTypeListUrl)}
                              onDelete={handleDelete}
                              onSubmit={handleUpdate}
                              key={searchState ? undefined : "search"}
                            />
                          );
                        }}
                      </ProductTypeOperations>
                    );
                  }}
                </AttributeSearchProvider>
              );
            }}
          </TypedProductTypeDetailsQuery>
        )}
      </Navigator>
    )}
  </Messages>
);
export default ProductTypeUpdate;
