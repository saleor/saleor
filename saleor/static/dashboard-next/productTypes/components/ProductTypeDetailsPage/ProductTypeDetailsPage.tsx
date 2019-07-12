import React from "react";

import AppHeader from "@saleor/components/AppHeader";
import CardSpacer from "@saleor/components/CardSpacer";
import { ConfirmButtonTransitionState } from "@saleor/components/ConfirmButton";
import Container from "@saleor/components/Container";
import { ControlledCheckbox } from "@saleor/components/ControlledCheckbox";
import Form from "@saleor/components/Form";
import Grid from "@saleor/components/Grid";
import PageHeader from "@saleor/components/PageHeader";
import SaveButtonBar from "@saleor/components/SaveButtonBar";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { AttributeTypeEnum, WeightUnitsEnum } from "../../../types/globalTypes";
import { ProductTypeDetails_productType } from "../../types/ProductTypeDetails";
import ProductTypeAttributes from "../ProductTypeAttributes/ProductTypeAttributes";
import ProductTypeDetails from "../ProductTypeDetails/ProductTypeDetails";
import ProductTypeShipping from "../ProductTypeShipping/ProductTypeShipping";
import ProductTypeTaxes from "../ProductTypeTaxes/ProductTypeTaxes";

interface ChoiceType {
  label: string;
  value: string;
}

export interface ProductTypeForm {
  name: string;
  hasVariants: boolean;
  isShippingRequired: boolean;
  taxType: {
    label: string;
    value: string;
  };
  productAttributes: ChoiceType[];
  variantAttributes: ChoiceType[];
  weight: number;
}

export interface ProductTypeDetailsPageProps {
  errors: Array<{
    field: string;
    message: string;
  }>;
  productType: ProductTypeDetails_productType;
  defaultWeightUnit: WeightUnitsEnum;
  disabled: boolean;
  pageTitle: string;
  saveButtonBarState: ConfirmButtonTransitionState;
  taxTypes: Array<{
    description: string;
    taxCode: string;
  }>;
  onAttributeAdd: (type: AttributeTypeEnum) => void;
  onAttributeDelete: (id: string, event: React.MouseEvent<any>) => void;
  onAttributeUpdate: (id: string) => void;
  onBack: () => void;
  onDelete: () => void;
  onSubmit: (data: ProductTypeForm) => void;
}

const ProductTypeDetailsPage: React.StatelessComponent<
  ProductTypeDetailsPageProps
> = ({
  defaultWeightUnit,
  disabled,
  errors,
  pageTitle,
  productType,
  saveButtonBarState,
  taxTypes,
  onAttributeAdd,
  onAttributeDelete,
  onAttributeUpdate,
  onBack,
  onDelete,
  onSubmit
}) => {
  const formInitialData: ProductTypeForm = {
    hasVariants:
      maybe(() => productType.hasVariants) !== undefined
        ? productType.hasVariants
        : false,
    isShippingRequired:
      maybe(() => productType.isShippingRequired) !== undefined
        ? productType.isShippingRequired
        : false,
    name: maybe(() => productType.name) !== undefined ? productType.name : "",
    productAttributes:
      maybe(() => productType.productAttributes) !== undefined
        ? productType.productAttributes.map(attribute => ({
            label: attribute.name,
            value: attribute.id
          }))
        : [],
    taxType:
      maybe(() => productType.taxType) !== undefined
        ? {
            label: productType.taxType.description,
            value: productType.taxType.taxCode
          }
        : {
            label: "",
            value: ""
          },
    variantAttributes:
      maybe(() => productType.variantAttributes) !== undefined
        ? productType.variantAttributes.map(attribute => ({
            label: attribute.name,
            value: attribute.id
          }))
        : [],
    weight: maybe(() => productType.weight.value)
  };
  return (
    <Form
      errors={errors}
      initial={formInitialData}
      onSubmit={onSubmit}
      confirmLeave
    >
      {({ change, data, hasChanged, submit }) => {
        return (
          <Container>
            <AppHeader onBack={onBack}>{i18n.t("Product Types")}</AppHeader>
            <PageHeader title={pageTitle} />
            <Grid>
              <div>
                <ProductTypeDetails
                  data={data}
                  disabled={disabled}
                  onChange={change}
                />
                <CardSpacer />
                <ProductTypeTaxes
                  disabled={disabled}
                  data={data}
                  taxTypes={maybe(() => taxTypes, [
                    { description: "", taxCode: "" }
                  ])}
                  onChange={change}
                />
                <CardSpacer />
                <ProductTypeAttributes
                  attributes={maybe(() => productType.productAttributes)}
                  type={AttributeTypeEnum.PRODUCT}
                  onAttributeAdd={onAttributeAdd}
                  onAttributeDelete={onAttributeDelete}
                  onAttributeUpdate={onAttributeUpdate}
                />
                <CardSpacer />
                <ControlledCheckbox
                  checked={data.hasVariants}
                  disabled={disabled}
                  label={i18n.t("This product type has variants")}
                  name="hasVariants"
                  onChange={change}
                />
                {data.hasVariants && (
                  <>
                    <CardSpacer />
                    <ProductTypeAttributes
                      attributes={maybe(() => productType.variantAttributes)}
                      type={AttributeTypeEnum.VARIANT}
                      onAttributeAdd={onAttributeAdd}
                      onAttributeDelete={onAttributeDelete}
                      onAttributeUpdate={onAttributeUpdate}
                    />
                  </>
                )}
              </div>
              <div>
                <ProductTypeShipping
                  disabled={disabled}
                  data={data}
                  defaultWeightUnit={defaultWeightUnit}
                  onChange={change}
                />
              </div>
            </Grid>
            <SaveButtonBar
              onCancel={onBack}
              onDelete={onDelete}
              onSave={submit}
              disabled={disabled || !hasChanged}
              state={saveButtonBarState}
            />
          </Container>
        );
      }}
    </Form>
  );
};
ProductTypeDetailsPage.displayName = "ProductTypeDetailsPage";
export default ProductTypeDetailsPage;
