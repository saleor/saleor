import * as React from "react";
import Navigator from "../../components/Navigator";

import { productTypeDetailsUrl, productTypeListUrl } from "..";
import Messages from "../../components/messages";
import { ProductTypeCreateMutation } from "../../gql-types";
import i18n from "../../i18n";
import ProductTypeDetailsPage, {
  ProductTypeForm
} from "../components/ProductTypeDetailsPage";
import {
  productTypeCreateMutation,
  TypedProductTypeCreateMutation
} from "../mutations";
import { searchAttributeQuery, TypedSearchAttributeQuery } from "../queries";

const taxRates = ["standard", "electronics", "food", "apparel"]; // FIXME: delet dis

const formData = {
  hasVariants: false,
  isShippingRequired: false,
  name: "",
  productAttributes: [],
  taxRate: undefined,
  variantAttributes: []
};

export const ProductTypeUpdate: React.StatelessComponent = () => (
  <Messages>
    {pushMessage => (
      <Navigator>
        {navigate => (
          <TypedSearchAttributeQuery query={searchAttributeQuery}>
            {searchAttribute => {
              const handleSearchAttribute = (search: string) =>
                search ? searchAttribute.refetch({ search }) : undefined;
              const handleCreateSuccess = (
                updateData: ProductTypeCreateMutation
              ) => {
                if (updateData.productTypeCreate.errors.length === 0) {
                  pushMessage({
                    text: i18n.t("Successfully created product type")
                  });
                  navigate(
                    productTypeDetailsUrl(
                      updateData.productTypeCreate.productType.id
                    )
                  );
                }
              };
              return (
                <TypedProductTypeCreateMutation
                  mutation={productTypeCreateMutation}
                  onCompleted={handleCreateSuccess}
                >
                  {(
                    createProductType,
                    { loading: loadingCreate, data: createProductTypeData }
                  ) => {
                    const handleCreate = (formData: ProductTypeForm) =>
                      createProductType({
                        variables: {
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
                        }
                      });
                    return (
                      <ProductTypeDetailsPage
                        disabled={loadingCreate}
                        pageTitle={i18n.t("Create Product Type", {
                          context: "page title"
                        })}
                        productType={formData}
                        productAttributes={[]}
                        variantAttributes={[]}
                        saveButtonBarState={
                          loadingCreate ? "loading" : "default"
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
                        onSubmit={handleCreate}
                      />
                    );
                  }}
                </TypedProductTypeCreateMutation>
              );
            }}
          </TypedSearchAttributeQuery>
        )}
      </Navigator>
    )}
  </Messages>
);
export default ProductTypeUpdate;
