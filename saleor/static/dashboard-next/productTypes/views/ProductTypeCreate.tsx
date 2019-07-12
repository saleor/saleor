import React from "react";

import { WindowTitle } from "@saleor/components/WindowTitle";
import useNavigator from "@saleor/hooks/useNavigator";
import useNotifier from "@saleor/hooks/useNotifier";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import ProductTypeCreatePage, {
  ProductTypeForm
} from "../components/ProductTypeCreatePage";
import { TypedProductTypeCreateMutation } from "../mutations";
import { TypedProductTypeCreateDataQuery } from "../queries";
import { ProductTypeCreate as ProductTypeCreateMutation } from "../types/ProductTypeCreate";
import { productTypeListUrl, productTypeUrl } from "../urls";

export const ProductTypeCreate: React.StatelessComponent = () => {
  const navigate = useNavigator();
  const notify = useNotifier();

  const handleCreateSuccess = (updateData: ProductTypeCreateMutation) => {
    if (updateData.productTypeCreate.errors.length === 0) {
      notify({
        text: i18n.t("Successfully created product type")
      });
      navigate(productTypeUrl(updateData.productTypeCreate.productType.id));
    }
  };
  return (
    <TypedProductTypeCreateMutation onCompleted={handleCreateSuccess}>
      {(
        createProductType,
        { loading: loadingCreate, data: createProductTypeData }
      ) => {
        const handleCreate = (formData: ProductTypeForm) =>
          createProductType({
            variables: {
              input: {
                hasVariants: false,
                isShippingRequired: formData.isShippingRequired,
                name: formData.name,
                taxCode: formData.taxType.value,
                weight: formData.weight
              }
            }
          });
        return (
          <TypedProductTypeCreateDataQuery displayLoader>
            {({ data, loading }) => (
              <>
                <WindowTitle title={i18n.t("Create product type")} />
                <ProductTypeCreatePage
                  defaultWeightUnit={maybe(() => data.shop.defaultWeightUnit)}
                  disabled={loadingCreate || loading}
                  errors={
                    createProductTypeData
                      ? createProductTypeData.productTypeCreate.errors
                      : undefined
                  }
                  pageTitle={i18n.t("Create Product Type", {
                    context: "page title"
                  })}
                  saveButtonBarState={loadingCreate ? "loading" : "default"}
                  taxTypes={maybe(() => data.taxTypes, [
                    {
                      __typename: "TaxType",
                      description: "",
                      taxCode: ""
                    }
                  ])}
                  onBack={() => navigate(productTypeListUrl())}
                  onSubmit={handleCreate}
                />
              </>
            )}
          </TypedProductTypeCreateDataQuery>
        );
      }}
    </TypedProductTypeCreateMutation>
  );
};
export default ProductTypeCreate;
