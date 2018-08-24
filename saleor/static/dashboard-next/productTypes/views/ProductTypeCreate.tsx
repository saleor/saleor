import * as React from "react";
import Navigator from "../../components/Navigator";

import { productTypeDetailsUrl, productTypeListUrl } from "..";
import Messages from "../../components/messages";
import { ProductTypeCreateMutation } from "../../gql-types";
import i18n from "../../i18n";
import ProductTypeDetailsPage, {
  ProductTypeForm
} from "../components/ProductTypeDetailsPage";
import { AttributeSearchProvider } from "../containers/AttributeSearch";
import { TypedProductTypeCreateMutation } from "../mutations";
import {
  productTypeCreateQuery,
  TypedProductTypeCreateDataQuery
} from "../queries";

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
          <TypedProductTypeCreateDataQuery query={productTypeCreateQuery}>
            {createData => (
              <AttributeSearchProvider>
                {(searchAttribute, searchState) => {
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
                            taxRates={
                              createData.data &&
                              createData.data.shop &&
                              createData.data.shop.taxRate &&
                              createData.data.shop.taxRate.reducedRates
                                ? createData.data.shop.taxRate.reducedRates
                                    .map(rate => rate.rateType)
                                    .concat(["standard"])
                                : ["standard"]
                            }
                            onAttributeSearch={searchAttribute}
                            onBack={() => navigate(productTypeListUrl)}
                            onSubmit={handleCreate}
                          />
                        );
                      }}
                    </TypedProductTypeCreateMutation>
                  );
                }}
              </AttributeSearchProvider>
            )}
          </TypedProductTypeCreateDataQuery>
        )}
      </Navigator>
    )}
  </Messages>
);
export default ProductTypeUpdate;
