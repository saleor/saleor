import React from "react";

import AppHeader from "@saleor/components/AppHeader";
import CardSpacer from "@saleor/components/CardSpacer";
import { ConfirmButtonTransitionState } from "@saleor/components/ConfirmButton";
import Container from "@saleor/components/Container";
import Form from "@saleor/components/Form";
import Grid from "@saleor/components/Grid";
import PageHeader from "@saleor/components/PageHeader";
import SaveButtonBar from "@saleor/components/SaveButtonBar";
import useFormset, {
  FormsetChange,
  FormsetData
} from "@saleor/hooks/useFormset";
import {
  getVariantAttributeErrors,
  getVariantAttributeInputFromProduct
} from "@saleor/products/utils/data";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { UserError } from "../../../types";
import { ProductVariantCreateData_product } from "../../types/ProductVariantCreateData";
import ProductVariantAttributes, {
  VariantAttributeInputData
} from "../ProductVariantAttributes";
import ProductVariantNavigation from "../ProductVariantNavigation";
import ProductVariantPrice from "../ProductVariantPrice";
import ProductVariantStock from "../ProductVariantStock";

interface ProductVariantCreatePageFormData {
  costPrice: string;
  images: string[];
  priceOverride: string;
  quantity: number;
  sku: string;
}

export interface ProductVariantCreatePageSubmitData
  extends ProductVariantCreatePageFormData {
  attributes: FormsetData<VariantAttributeInputData>;
}

interface ProductVariantCreatePageProps {
  currencySymbol: string;
  errors: UserError[];
  header: string;
  loading: boolean;
  product: ProductVariantCreateData_product;
  saveButtonBarState: ConfirmButtonTransitionState;
  onBack: () => void;
  onSubmit: (data: ProductVariantCreatePageSubmitData) => void;
  onVariantClick: (variantId: string) => void;
}

const ProductVariantCreatePage: React.FC<ProductVariantCreatePageProps> = ({
  currencySymbol,
  errors: formErrors,
  loading,
  header,
  product,
  saveButtonBarState,
  onBack,
  onSubmit,
  onVariantClick
}) => {
  const attributeInput = React.useMemo(
    () => getVariantAttributeInputFromProduct(product),
    [product]
  );
  const { change: changeAttributeData, data: attributes } = useFormset(
    attributeInput
  );

  const initialForm = {
    attributes: maybe(
      () =>
        product.productType.variantAttributes.map(attribute => ({
          name: attribute.name,
          slug: attribute.slug,
          values: [""]
        })),
      []
    ),
    costPrice: "",
    images: maybe(() => product.images.map(image => image.id)),
    priceOverride: "",
    quantity: 0,
    sku: ""
  };

  const handleSubmit = (data: ProductVariantCreatePageFormData) =>
    onSubmit({
      ...data,
      attributes
    });

  return (
    <Form initial={initialForm} errors={formErrors} onSubmit={handleSubmit}>
      {({ change, data, errors, hasChanged, submit, triggerChange }) => {
        const handleAttributeChange: FormsetChange = (id, value) => {
          changeAttributeData(id, value);
          triggerChange();
        };

        return (
          <Container>
            <AppHeader onBack={onBack}>{maybe(() => product.name)}</AppHeader>
            <PageHeader title={header} />
            <Grid variant="inverted">
              <div>
                <ProductVariantNavigation
                  fallbackThumbnail={maybe(() => product.thumbnail.url)}
                  variants={maybe(() => product.variants)}
                  onRowClick={(variantId: string) => {
                    if (product && product.variants) {
                      return onVariantClick(variantId);
                    }
                  }}
                />
              </div>
              <div>
                <ProductVariantAttributes
                  attributes={attributes}
                  disabled={loading}
                  errors={getVariantAttributeErrors(
                    formErrors,
                    maybe(() => product.productType.variantAttributes)
                  )}
                  onChange={handleAttributeChange}
                />
                <CardSpacer />
                <ProductVariantPrice
                  errors={errors}
                  priceOverride={data.priceOverride}
                  currencySymbol={currencySymbol}
                  costPrice={data.costPrice}
                  loading={loading}
                  onChange={change}
                />
                <CardSpacer />
                <ProductVariantStock
                  errors={errors}
                  sku={data.sku}
                  quantity={data.quantity}
                  loading={loading}
                  onChange={change}
                />
              </div>
            </Grid>
            <SaveButtonBar
              disabled={loading || !onSubmit || !hasChanged}
              labels={{
                delete: i18n.t("Remove variant"),
                save: i18n.t("Save variant")
              }}
              state={saveButtonBarState}
              onCancel={onBack}
              onSave={submit}
            />
          </Container>
        );
      }}
    </Form>
  );
};
ProductVariantCreatePage.displayName = "ProductVariantCreatePage";
export default ProductVariantCreatePage;
