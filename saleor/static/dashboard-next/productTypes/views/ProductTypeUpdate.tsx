import * as React from "react";
import Navigator from "../../components/Navigator";

import { productTypeListUrl } from "..";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Messages from "../../components/messages";
import {
  ProductTypeDeleteMutation,
  ProductTypeUpdateMutation
} from "../../gql-types";
import i18n from "../../i18n";
import ProductTypeDetailsPage, {
  ProductTypeForm
} from "../components/ProductTypeDetailsPage";
import ProductTypeOperations from "../containers/ProductTypeOperations";
import {
  productTypeDetailsQuery,
  searchAttributeQuery,
  TypedProductTypeDetailsQuery,
  TypedSearchAttributeQuery
} from "../queries";

const taxRates = ["standard", "electronics", "food", "apparel"]; // FIXME: delet dis

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
          <TypedProductTypeDetailsQuery
            query={productTypeDetailsQuery}
            variables={{ id }}
          >
            {({ data, error, loading: dataLoading }) => {
              if (error) {
                return (
                  <ErrorMessageCard
                    message={i18n.t("Something went terribly wrong")}
                  />
                );
              }
              return (
                <TypedSearchAttributeQuery query={searchAttributeQuery}>
                  {searchAttribute => {
                    const handleSearchAttribute = (search: string) =>
                      search ? searchAttribute.refetch({ search }) : undefined;
                    const handleDeleteSuccess = (
                      deleteData: ProductTypeDeleteMutation
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
                                variantAttributes: formData.variantAttributes.map(
                                  choice => choice.value
                                )
                              }
                            });
                          };
                          const loading = mutationLoading || dataLoading;
                          return (
                            <ProductTypeDetailsPage
                              disabled={false}
                              productType={data ? data.productType : undefined}
                              productAttributes={
                                data &&
                                data.productType &&
                                data.productType.productAttributes &&
                                data.productType.productAttributes.edges
                                  ? data.productType.productAttributes.edges.map(
                                      edge => edge.node
                                    )
                                  : undefined
                              }
                              variantAttributes={
                                data &&
                                data.productType &&
                                data.productType.variantAttributes &&
                                data.productType.variantAttributes.edges
                                  ? data.productType.variantAttributes.edges.map(
                                      edge => edge.node
                                    )
                                  : undefined
                              }
                              saveButtonBarState={
                                loading ? "loading" : "default"
                              }
                              searchLoading={searchAttribute.loading}
                              searchResults={
                                searchAttribute.data &&
                                searchAttribute.data.attributes
                                  ? searchAttribute.data.attributes.edges.map(
                                      edge => edge.node
                                    )
                                  : []
                              }
                              taxRates={taxRates}
                              onAttributeSearch={handleSearchAttribute}
                              onBack={() => navigate(productTypeListUrl)}
                              onDelete={handleDelete}
                              onSubmit={handleUpdate}
                            />
                          );
                        }}
                      </ProductTypeOperations>
                    );
                  }}
                </TypedSearchAttributeQuery>
              );
            }}
          </TypedProductTypeDetailsQuery>
        )}
      </Navigator>
    )}
  </Messages>
);
export default ProductTypeUpdate;
