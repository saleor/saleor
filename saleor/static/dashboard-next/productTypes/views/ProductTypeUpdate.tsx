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
import {
  productTypeDetailsQuery,
  TypedProductTypeDetailsQuery
} from "../queries";
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
                                ...formData,
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
                              disabled={loading}
                              errors={errors}
                              pageTitle={
                                data && data.productType
                                  ? data.productType.name
                                  : undefined
                              }
                              productType={data ? data.productType : undefined}
                              productAttributes={maybe(
                                () => data.productType.productAttributes,
                                []
                              )}
                              variantAttributes={maybe(
                                () => data.productType.variantAttributes,
                                []
                              )}
                              saveButtonBarState={
                                loading ? "loading" : "default"
                              }
                              searchLoading={
                                searchState ? searchState.loading : false
                              }
                              searchResults={
                                searchState &&
                                searchState.data &&
                                searchState.data.attributes
                                  ? searchState.data.attributes.edges.map(
                                      edge => edge.node
                                    )
                                  : []
                              }
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
