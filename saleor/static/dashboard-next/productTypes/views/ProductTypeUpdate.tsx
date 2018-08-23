import * as React from "react";
import Navigator from "../../components/Navigator";

import { productTypeListUrl } from "..";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Messages from "../../components/messages";
import i18n from "../../i18n";
import ProductTypeDetailsPage from "../components/ProductTypeDetailsPage";
import ProductTypeOperations from "../containers/ProductTypeOperations";
import {
  productTypeDetailsQuery,
  searchAttributeQuery,
  TypedProductTypeDetailsQuery,
  TypedSearchAttributeQuery
} from "../queries";
import { ProductTypeDeleteMutation } from "../../gql-types";

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
                    return (
                      <ProductTypeOperations
                        id={id}
                        onDelete={handleDeleteSuccess}
                      >
                        {({ deleteProductType, loading: mutationLoading }) => {
                          const handleDelete = () =>
                            deleteProductType.mutate({ id });
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
                              onSubmit={() => undefined}
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
