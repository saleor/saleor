import * as React from "react";

import ErrorMessageCard from "../../components/ErrorMessageCard";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import { ProductCreateMutation } from "../../gql-types";
import i18n from "../../i18n";
import ProductCreatePage from "../components/ProductCreatePage";
import { productListUrl, productUrl } from "../index";
import {
  productCreateMutation,
  TypedProductCreateMutation
} from "../mutations";
import { productCreateQuery, TypedProductCreateQuery } from "../queries";

interface ProductUpdateProps {
  id: string;
}

export const ProductUpdate: React.StatelessComponent<ProductUpdateProps> = ({
  id
}) => (
  <Messages>
    {pushMessage => {
      return (
        <Navigator>
          {navigate => {
            const handleAttributesEdit = () => {};
            const handleBack = () => navigate(productListUrl);

            return (
              <TypedProductCreateQuery query={productCreateQuery}>
                {({ data, error, loading }) => {
                  const handleError = () =>
                    pushMessage({ text: i18n.t("Something went wrong") });
                  const handleSuccess = (data: ProductCreateMutation) => {
                    if (data.productCreate.errors.length === 0) {
                      pushMessage({ text: i18n.t("Product created") });
                      navigate(productUrl(data.productCreate.product.id));
                    }
                  };

                  if (error) {
                    return (
                      <ErrorMessageCard
                        message={i18n.t("Something went wrong")}
                      />
                    );
                  }

                  return (
                    <TypedProductCreateMutation
                      mutation={productCreateMutation}
                      onCompleted={handleSuccess}
                      onError={handleError}
                    >
                      {(
                        productCreate,
                        {
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
                              isFeatured: formData.featured,
                              isPublished: formData.available,
                              name: formData.name,
                              price: formData.price,
                              productType: formData.productType.value.id
                            }
                          });
                        };

                        const disabled = loading || productCreateDataLoading;
                        return (
                          <ProductCreatePage
                            categories={
                              data && data.categories
                                ? data.categories.edges.map(edge => edge.node)
                                : undefined
                            }
                            collections={
                              data && data.collections
                                ? data.collections.edges.map(edge => edge.node)
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
                                ? data.productTypes.edges.map(edge => edge.node)
                                : undefined
                            }
                            onAttributesEdit={handleAttributesEdit}
                            onBack={handleBack}
                            onSubmit={handleSubmit}
                          />
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
);
export default ProductUpdate;
