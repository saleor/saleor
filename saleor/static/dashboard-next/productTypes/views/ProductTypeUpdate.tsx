import * as React from "react";
import Navigator from "../../components/Navigator";

import { productTypeListUrl } from "..";
import Messages from "../../components/messages";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import ProductTypeDetailsPage, {
  ProductTypeForm
} from "../components/ProductTypeDetailsPage";
import ProductTypeOperations from "../containers/ProductTypeOperations";
import { TypedProductTypeDetailsQuery } from "../queries";
import { AttributeCreate } from "../types/AttributeCreate";
import { AttributeDelete } from "../types/AttributeDelete";
import { AttributeUpdate } from "../types/AttributeUpdate";
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
            {({ data, loading: dataLoading }) => {
              const handleAttributeCreateSuccess = (data: AttributeCreate) => {
                if (!maybe(() => data.attributeCreate.errors.length)) {
                  pushMessage({
                    text: i18n.t("Attribute created", {
                      context: "notification"
                    })
                  });
                }
              };
              const handleAttributeDeleteSuccess = (data: AttributeDelete) => {
                if (!maybe(() => data.attributeDelete.errors.length)) {
                  pushMessage({
                    text: i18n.t("Attribute deleted", {
                      context: "notification"
                    })
                  });
                }
              };
              const handleAttributeUpdateSuccess = (data: AttributeUpdate) => {
                if (!maybe(() => data.attributeUpdate.errors.length)) {
                  pushMessage({
                    text: i18n.t("Attribute updated", {
                      context: "notification"
                    })
                  });
                }
              };
              const handleProductTypeDeleteSuccess = (
                deleteData: ProductTypeDelete
              ) => {
                if (deleteData.productTypeDelete.errors.length === 0) {
                  pushMessage({
                    text: i18n.t("Product type deleted", {
                      context: "notification"
                    })
                  });
                  navigate(productTypeListUrl);
                }
              };
              const handleProductTypeUpdateSuccess = (
                updateData: ProductTypeUpdateMutation
              ) => {
                if (updateData.productTypeUpdate.errors.length === 0) {
                  pushMessage({
                    text: i18n.t("Product type updated", {
                      context: "notification"
                    })
                  });
                }
              };

              return (
                <ProductTypeOperations
                  id={id}
                  onAttributeCreate={handleAttributeCreateSuccess}
                  onAttributeDelete={handleAttributeDeleteSuccess}
                  onAttributeUpdate={handleAttributeUpdateSuccess}
                  onProductTypeDelete={handleProductTypeDeleteSuccess}
                  onProductTypeUpdate={handleProductTypeUpdateSuccess}
                >
                  {({
                    deleteProductType,
                    errors,
                    loading: mutationLoading,
                    updateProductType
                  }) => {
                    const handleProductTypeDelete = () =>
                      deleteProductType.mutate({ id });
                    const handleProductTypeUpdate = (
                      formData: ProductTypeForm
                    ) => {
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
                        saveButtonBarState={loading ? "loading" : "default"}
                        onAttributeAdd={() => undefined}
                        onAttributeUpdate={() => undefined}
                        onBack={() => navigate(productTypeListUrl)}
                        onDelete={handleProductTypeDelete}
                        onSubmit={handleProductTypeUpdate}
                      />
                    );
                  }}
                </ProductTypeOperations>
              );
            }}
          </TypedProductTypeDetailsQuery>
        )}
      </Navigator>
    )}
  </Messages>
);
export default ProductTypeUpdate;
